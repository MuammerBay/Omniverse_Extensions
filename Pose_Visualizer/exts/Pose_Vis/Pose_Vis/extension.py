'''
Built on top of: "SDG 2D bounding box metadata viewer extension"
Credits: Sirens
'''



import omni.ext
import omni.ui as ui
import matplotlib.pyplot as plt
from PIL import Image
import os
import json
import re
import tempfile
from omni.kit.window.filepicker import FilePickerDialog
import random


class Pose_Vis(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[Pose_Vis] Extension started")

        self.files = []
        self.current_index = -1
        self.temp_plot_path = None
        self.type_labels = []
        self.object_containers = []

        self.init_styles()
        self.create_window()

    def init_styles(self):
        self.frame_style = {
            "background_color": 0xFF747474,
            "border_radius": 4,
            "padding": 8,
            "margin": 2
        }

        self.label_style = {
            "font_size": 14,
            "color": 0xFFFFFFFF,
            "width": 150
        }

        self.button_style = {
            "background_color": 0xFF747474,
            "color": 0xFFFFFFFF,
            "height": 20,
            "font_size": 14
        }

        self.header_style = {
            "font_size": 20,
            "color": 0xFF00B976,
            "bold": True
        }

    def create_window(self):
        self._window = ui.Window("SDG 3 Bounding Box Viewer", width=1300, height=900)

        with self._window.frame:
            with ui.HStack():
                # Left side controls (fixed width)
                with ui.VStack(width=200):
                    self.create_description()
                    self.create_controls()
                    self.create_frame_section()
                    self.create_credit_info()



                # Right side image (fills remaining space)
                with ui.VStack():
                    self.plot_widget = ui.Image(
                        style={
                            "border_width": 1,
                            "border_color": 0xFF00B976,
                            "margin": 4
                        }
                    )


    def create_description(self):
        with ui.Frame(style=self.frame_style):
            with ui.VStack(spacing=1, height=1):
                ui.Label("3D Pose Visualizer\n", style=self.header_style)
                ui.Label("Select an output folder based on PoseWriter()\nExample Doc:\n'Pose Estimation Synthetic Data Generation'", style=self.label_style)
                self.file_label = ui.Label("", style=self.label_style)

    def create_controls(self):
        with ui.Frame(style=self.frame_style):
            with ui.VStack(spacing=5, height=1):
                ui.Button("Select Folder", clicked_fn=self.select_folder,
                          style=self.button_style, width=150)
                self.prev_button = ui.Button("Previous", clicked_fn=self.previous_file,
                                              enabled=False, style=self.button_style, width=150)
                self.next_button = ui.Button("Next", clicked_fn=self.next_file,
                                              enabled=False, style=self.button_style, width=150)

    def create_frame_section(self):
        with ui.Frame(style=self.frame_style):
            with ui.VStack(spacing=5, height=1):
                ui.Label("Current Frame", style=self.header_style)
                self.file_label = ui.Label("", style=self.label_style)
                ui.Label("Go to Frame: (integers in valid range)", style=self.label_style)
                with ui.HStack(spacing=5):
                    self.frame_input = ui.StringField(width=75)
                    ui.Button("Go", clicked_fn=self.jump_to_frame,
                              style=self.button_style, width=75)
                    

    def create_credit_info(self):

        with ui.HStack(height=50, spacing=10):
            ui.Label(
                '\n\n\nBuilt on top of: \n"SDG 2D bounding box metadata viewer extension"\nCredits: Sirens',
                style={
                    "font_size": 12,
                    "color": 0xFFAAAAAA,  # Light gray text
                    "alignment": ui.Alignment.LEFT  # Align text to the left
                }
            )

    def visualize_image_with_json(self, image_file, json_file):
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            img = Image.open(image_file)
            ax.imshow(img)
            ax.axis("off")
            ax.set_title("3D Poses of Objects")

            # Reset all object containers and labels
            for container in self.object_containers:
                container.visible = False
            for label in self.type_labels:
                label.text = ""

            # Extract frame number from the file name
            frame_num = os.path.splitext(os.path.basename(image_file))[0]

            # Load JSON data
            with open(json_file, "r") as jf:
                data = json.load(jf)

            objects = data.get("objects", [])

            # Always update the frame label
            self.file_label.text = f"Frame: {frame_num}"

            if not objects:
                print(f"Warning: No objects found in JSON for frame {frame_num}")
                # Save and display the image even without objects
                temp_dir = tempfile.gettempdir()
                self.temp_plot_path = os.path.join(temp_dir, f"plot_{os.getpid()}_{self.current_index}.png")
                fig.savefig(self.temp_plot_path, bbox_inches="tight", dpi=100, pad_inches=0)
                plt.close(fig)

                if os.path.exists(self.temp_plot_path):
                    self.plot_widget.source_url = self.temp_plot_path
                return

            # Define keypoint connections for a cuboid
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Front face
                (4, 5), (5, 6), (6, 7), (7, 4),  # Back face
                (0, 4), (1, 5), (2, 6), (3, 7)   # Edges connecting front and back
            ]

            # Predefined vivid colors for classes
            vivid_colors = ["red", "blue", "green", "orange", "purple"]
            colors = {}
            visibility_map = {}  # Store max visibility for each class
            unique_classes = []

            for obj in objects:
                class_name = obj.get("class", "Unknown")
                visibility = obj.get("visibility", 0)  # Get visibility or default to 0

                if class_name not in colors:
                    colors[class_name] = vivid_colors[len(colors) % len(vivid_colors)]
                    unique_classes.append(class_name)  # Add to unique classes for the legend
                    visibility_map[class_name] = visibility
                else:
                    # Update max visibility for the class
                    visibility_map[class_name] = max(visibility_map[class_name], visibility)

                cuboid = obj.get("projected_cuboid", [])
                if len(cuboid) < 8:
                    continue

                # Draw cuboid connections
                for start, end in connections:
                    x = [cuboid[start][0], cuboid[end][0]]
                    y = [cuboid[start][1], cuboid[end][1]]
                    ax.plot(x, y, 'o-', color=colors[class_name])

            # Create a legend with visibility information
            handles = [
                plt.Line2D([0], [0], color=colors[cls], lw=2, 
                        label=f"{cls.replace('_', ' ')} (Visib.: {visibility_map[cls]:.2f})")
                for cls in unique_classes
            ]
            ax.legend(handles=handles, loc="upper right", title="Classes")

            # Save and display the plot
            temp_dir = tempfile.gettempdir()
            self.temp_plot_path = os.path.join(temp_dir, f"plot_{os.getpid()}_{self.current_index}.png")
            fig.savefig(self.temp_plot_path, bbox_inches="tight", dpi=100, pad_inches=0)
            plt.close(fig)

            if os.path.exists(self.temp_plot_path):
                self.plot_widget.source_url = self.temp_plot_path

        except Exception as e:
            print(f"Error visualizing frame {frame_num}: {e}")
            self.file_label.text = f"Error: {e}"


    def select_folder(self):
        self.file_picker = FilePickerDialog(
            title="Select Folder",
            click_apply_handler=self.process_folder,
            allow_folders=True,
            apply_button_label="Select"
        )
        self.file_picker.show()

    def process_folder(self, file_name, folder_path, *args):
        if folder_path:
            self.cleanup_temp_file()
            self.files = self.scan_folder(folder_path)
            if self.files:
                self.current_index = 0
                self.update_buttons()
                self.refresh_plot()
            else:
                self.file_label.text = "No valid files found"

    def scan_folder(self, folder_path):
        valid_files = []

        for file in os.listdir(folder_path):
            if file.endswith(".json"):
                base_name = os.path.splitext(file)[0]
                json_file = os.path.join(folder_path, file)
                image_file = os.path.join(folder_path, f"{base_name}.png")
                if os.path.exists(image_file):
                    valid_files.append((image_file, json_file))
                else:
                    print(f"Warning: Missing PNG for {file}")

        valid_files.sort(key=lambda x: int(re.search(r"(\d+)", os.path.basename(x[0])).group(1)))
        return valid_files

    def jump_to_frame(self):
        try:
            frame_num = int(self.frame_input.model.get_value_as_string())
            if 0 <= frame_num < len(self.files):
                self.current_index = frame_num
                self.update_buttons()
                self.refresh_plot()
        except ValueError:
            print("Invalid frame number")

    def next_file(self):
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.update_buttons()
            self.refresh_plot()

    def previous_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            self.refresh_plot()

    def refresh_plot(self):
        try:
            current_file_pair = self.files[self.current_index]
            self.cleanup_temp_file()
            self.visualize_image_with_json(*current_file_pair)
        except Exception as e:
            print(f"Error refreshing plot: {e}")
            self.file_label.text = f"Error: {e}"

    def update_buttons(self):
        self.prev_button.enabled = self.current_index > 0
        self.next_button.enabled = self.current_index < len(self.files) - 1

    def cleanup_temp_file(self):
        if self.temp_plot_path and os.path.exists(self.temp_plot_path):
            try:
                os.remove(self.temp_plot_path)
            except Exception as e:
                print(f"Error cleaning up temporary file: {e}")

    def on_shutdown(self):
        self.cleanup_temp_file()
        print("[Pose_Vis] Extension shutdown")
