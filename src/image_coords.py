import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.widgets import Button, TextBox, RadioButtons
import matplotlib.gridspec as gridspec
import yaml
import os

class CoordinateViewer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.dots = {}  # Stores '0', '1', '2', '3' -> artist
        self.coord_texts = {} # Stores '0', '1', '2', '3' -> text artist
        
        self.groups = {} # {group_name: {key: (x, y)}}
        self.current_group_name = None
        self.yaml_file = os.path.join(os.path.dirname(__file__), '..', 'output', "groups.yaml")
        
        # Scrollable list state
        self.group_scroll_start = 0
        self.max_visible_groups = 8
        
        # Scrollable list state
        self.group_scroll_start = 0
        self.max_visible_groups = 8

        # Load existing groups if file exists
        self.load_groups_from_file()
        
        # Load the image
        try:
            self.img = mpimg.imread(self.image_path)
        except FileNotFoundError:
            print(f"Error: '{self.image_path}' not found in the current directory.")
            self.img = None
            return

        self.setup_plot()
    def tuple_constructor(loader, node):
        return tuple(loader.construct_sequence(node))

    yaml.SafeLoader.add_constructor(
        "tag:yaml.org,2002:python/tuple",
        tuple_constructor
    )

    def load_groups_from_file(self):
        if os.path.exists(self.yaml_file):
            try:
                with open(self.yaml_file, 'r') as f:
                    self.groups = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading yaml: {e}")
                self.groups = {}
        else:
            self.groups = {}

    def setup_plot(self):
        # Create figure
        self.fig = plt.figure(figsize=(14, 8))
        
        # Layout: Left Control Panel (1 part), Right Image Panel (3 parts)
        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 3])
        
        # Right Panel: Image
        self.ax_img = self.fig.add_subplot(gs[1])
        self.ax_img.imshow(self.img)
        self.ax_img.set_title("Move: coords | 0/1/2/3: plot dot")
        
        # Left Panel: Controls
        # We will subdivide the left panel or just use figure coordinates for widgets
        # Using figure coordinates for widgets is often easier for custom layouts
        self.ax_ctrl = self.fig.add_subplot(gs[0])
        self.ax_ctrl.axis('off') # Hide axis for the control panel container

        # --- UI LAYOUT ---
        # Definitions of positions (left, bottom, width, height) in figure fraction
        
        # 1. Saved Groups (Dropdown/Radio)
        self.fig.text(0.02, 0.95, "Saved Groups:", fontsize=12, fontweight='bold')
        
        # RadioButtons need an axes
        rect_radio = [0.02, 0.75, 0.2, 0.18]
        self.ax_radio = self.fig.add_axes(rect_radio)
        self.ax_radio.set_facecolor('#f0f0f0')
        
        self.refresh_radio_buttons()

        # 2. Coordinates Display
        self.fig.text(0.02, 0.70, "Coordinates:", fontsize=12, fontweight='bold')
        # We'll use the ax_ctrl for drawing the boxes and text manually or just figure text
        # Let's use figure text for simplicity as before, but nicer
        
        labels = {
            '0': ('Origin', 'black'),
            '1': ('Red', 'red'),
            '2': ('Blue', 'blue'),
            '3': ('Black', 'black')
        }
        
        start_y = 0.65
        for key, (label, color) in labels.items():
            # Add a bounding box visual (using a bbox kwarg in text)
            t = self.fig.text(0.02, start_y, f"{label}: None", 
                              color=color, fontsize=11,
                              bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
            self.coord_texts[key] = t
            start_y -= 0.06

        # 3. Current Group Label
        self.lbl_current_group = self.fig.text(0.02, start_y - 0.05, "Current Group: None", 
                                               fontsize=11, bbox=dict(facecolor='magenta', alpha=0.5))

        # 4. New Group Entry
        rect_text = [0.02, start_y - 0.15, 0.15, 0.04] # bbox for textbox
        self.ax_text_box = self.fig.add_axes(rect_text)
        self.text_box = TextBox(self.ax_text_box, '', initial="NewGroup")
        self.fig.text(0.18, start_y - 0.13, "Group", fontsize=12) # Label to the right
        
        # 5. Buttons
        # Row 1: New Group, Save Group
        btn_y_row1 = start_y - 0.22
        
        ax_btn_new = self.fig.add_axes([0.02, btn_y_row1, 0.10, 0.05])
        self.btn_new = Button(ax_btn_new, 'New Group')
        self.btn_new.on_clicked(self.create_new_group)
        
        ax_btn_save = self.fig.add_axes([0.13, btn_y_row1, 0.10, 0.05])
        self.btn_save = Button(ax_btn_save, 'Save Group')
        self.btn_save.on_clicked(self.save_current_group)
        
        # Row 2: Reset View, Save All
        btn_y_row2 = btn_y_row1 - 0.07
        
        ax_btn_reset = self.fig.add_axes([0.02, btn_btn_y_row2 := btn_y_row2, 0.10, 0.05])
        self.btn_reset = Button(ax_btn_reset, 'Reset View')
        self.btn_reset.on_clicked(self.reset_view)
        
        ax_btn_save_all = self.fig.add_axes([0.13, btn_y_row2, 0.10, 0.05])
        self.btn_save_all = Button(ax_btn_save_all, 'Save All')
        self.btn_save_all.on_clicked(self.save_all_groups)

        # Row 3: Load Group
        btn_y_row3 = btn_y_row2 - 0.07
        ax_btn_load = self.fig.add_axes([0.02, btn_y_row3, 0.10, 0.05])
        self.btn_load = Button(ax_btn_load, 'Load Group')
        self.btn_load.on_clicked(self.load_all_groups)

        # Connect events
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        plt.subplots_adjust(left=0.25, right=0.95) # Adjust main plot to not overlap left controls
        
        # Scroll event
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        plt.show()

    # --- Event Handlers ---

    def on_scroll(self, event):
        # Check if mouse is over the radio button axes
        if event.inaxes == self.ax_radio:
            group_list = list(self.groups.keys())
            if not group_list:
                return
                
            step = int(event.step)
            # Scroll up (positive step) -> decrease start index
            # Scroll down (negative step) -> increase start index
            if step > 0:
                self.group_scroll_start = max(0, self.group_scroll_start - 1)
            else:
                 max_start = max(0, len(group_list) - self.max_visible_groups)
                 self.group_scroll_start = min(max_start, self.group_scroll_start + 1)
            
            self.refresh_radio_buttons()

    def on_move(self, event):
        if event.inaxes == self.ax_img:
            self.ax_img.set_xlabel(f'x={int(event.xdata)}, y={int(event.ydata)}')
            self.fig.canvas.draw_idle()

    def on_key(self, event):
        if event.inaxes == self.ax_img and event.key in ['0', '1', '2', '3']:
            # Remove existing dot logic
            if event.key in self.dots:
                self.dots[event.key].remove()
            
            color_map = {'0': 'white', '1': 'red', '2': 'blue', '3': 'black'}
            display_names = {'0': 'Origin', '1': 'Red', '2': 'Blue', '3': 'Black'}
            
            color_name = color_map[event.key]
            display_name = display_names[event.key]
            
            lines = self.ax_img.plot(event.xdata, event.ydata, color=color_name, marker='o', markersize=5)
            self.dots[event.key] = lines[0]
            
            if event.key in self.coord_texts:
                self.coord_texts[event.key].set_text(f"{display_name}: ({int(event.xdata)}, {int(event.ydata)})")
                
            print(f'{color_name}({int(event.xdata)}, {int(event.ydata)})')
            self.fig.canvas.draw_idle()

    # --- Button Logic ---

    def create_new_group(self, event):
        name = self.text_box.text
        if name in self.groups:
            print(f"Error: Group '{name}' already exists.")
            return
        
        # Create new empty group
        self.groups[name] = {}
        self.current_group_name = name
        self.update_group_info(name)
        
        # Update UI: Text Label and Radio list
        self.lbl_current_group.set_text(f"Current Group: {name}")
        self.refresh_radio_buttons()

    def save_current_group(self, event):
        if not self.current_group_name:
            print("Error: No current group selected.")
            return
        
        # Save current dots to memory
        group_data = {}
        # We need to extract coordinates from existing dots
        # self.dots maps key -> Line2D
        for key, line in self.dots.items():
            x = line.get_xdata()[0]
            y = line.get_ydata()[0]
            
            # Map key '0'-'3' to semantic names
            display_names = {'0': 'Origin', '1': 'Red', '2': 'Blue', '3': 'Black'}
            semantic_key = display_names.get(key, key)
            
            group_data[semantic_key] = [float(x), float(y)] # Store as list
            
        self.groups[self.current_group_name] = group_data
        print(f"Group '{self.current_group_name}' saved to memory.")

    def save_all_groups(self, event):
        try:
            with open(self.yaml_file, 'w') as f:
                yaml.dump(self.groups, f)
            print(f"All groups saved to {self.yaml_file}.")
        except Exception as e:
            print(f"Error saving to file: {e}")

    def load_all_groups(self, event):
        self.load_groups_from_file()
        self.refresh_radio_buttons()
        print("Groups reloaded from file.")

    def reset_view(self, event):
        self.ax_img.autoscale()
        self.fig.canvas.draw_idle()

    def select_group(self, label):
        if label == "No Groups":
            return
            
        self.current_group_name = label
        self.lbl_current_group.set_text(f"Current Group: {label}")
        self.update_group_info(label)

    def refresh_radio_buttons(self):
        # Re-create radio buttons with new list
        self.ax_radio.clear()
        all_groups = list(self.groups.keys())
        
        if not all_groups:
            visible_groups = ["No Groups"]
            active_idx = 0
            self.group_scroll_start = 0
        else:
            # Slice the list based on scroll position
            end_idx = min(len(all_groups), self.group_scroll_start + self.max_visible_groups)
            visible_groups = all_groups[self.group_scroll_start : end_idx]
            
            # Determine active index relative to visible list
            if self.current_group_name in visible_groups:
                active_idx = visible_groups.index(self.current_group_name)
            else:
                active_idx = 0 # Default to first item if selection is not visible

        self.radio = RadioButtons(self.ax_radio, visible_groups, active=active_idx)
        self.radio.on_clicked(self.select_group)
        self.fig.canvas.draw_idle()

    def update_group_info(self, group_name):
        # Clear current dots
        for dot in self.dots.values():
            dot.remove()
        self.dots = {}
        
        # Reset text
        display_names = {'0': 'Origin', '1': 'Red', '2': 'Blue', '3': 'Black'}
        for key in self.coord_texts:
            self.coord_texts[key].set_text(f"{display_names[key]}: None")

        # Load dots from group
        group_data = self.groups.get(group_name, {})
        color_map = {'0': 'white', '1': 'red', '2': 'blue', '3': 'black'}
        
        for key, coords in group_data.items():
             x, y = coords
             
             # Map semantic name to key if necessary, or numeric key to key
             # Reverse map: Name -> Key
             name_to_key = {'Origin': '0', 'Red': '1', 'Blue': '2', 'Black': '3'}
             
             # If key is already '0', '1' etc (old format), keep it. If 'Red', map to '1'.
             internal_key = key
             if key in name_to_key:
                 internal_key = name_to_key[key]
             
             color_name = color_map.get(internal_key, 'black')
             
             lines = self.ax_img.plot(x, y, color=color_name, marker='o', markersize=5)
             self.dots[internal_key] = lines[0]
             
             # Update Text
             if internal_key in self.coord_texts:
                 self.coord_texts[internal_key].set_text(f"{display_names[internal_key]}: ({int(x)}, {int(y)})")
                 
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Nightingale.png')
    CoordinateViewer(image_path)
