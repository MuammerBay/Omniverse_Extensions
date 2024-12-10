# extension.py 

# Extension Tutorial
# Credits: Sirens

import omni.ext 
import omni.ui as ui 
from .utils import multiply # Import from utils.py 
from .tasks import reset_label, increment_count # Import from tasks.py 
 
class StudyGroupSimExtension(omni.ext.IExt): 
    def on_startup(self, ext_id): 
        print("[study.group.sim] study group sim startup") 
        self._count = 0 
        self._window = ui.Window("My Window", width=300, height=300) 
        with self._window.frame: 
            with ui.VStack(): 
 
                label = ui.Label("") 
 
                def on_click(): 
                    self._count = increment_count(self._count) # Call from tasks.py 
                    label.text = f"count: {self._count}" 
 
                def on_reset(): 
                    self._count = 0 
                    label.text = reset_label() # Call from tasks.py 
 
                def on_multiply(): 
                    result = multiply(self._count, 10) # Call from utils.py 
                    label.text = f"{self._count} x 10 = {result}" # Display the result 
                     
                ui.Button("Add", clicked_fn=on_click) 
                ui.Button("Reset", clicked_fn=on_reset) 
                ui.Button("Multiply by 10", clicked_fn=on_multiply) # New button 
 
    def on_shutdown(self): 
        print("[study.group.sim] study group sim shutdown")