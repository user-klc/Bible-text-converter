# main.py
import sqlite3
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivy.lang import Builder
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
# Removed: from kivymd.uix.separator import MDSeparator # Not available in KivyMD 1.2.0
from kivymd.toast import toast
from kivy.metrics import dp
import os

# Define colour variables
sage = (0.584, 0.773, 0.584, 1)  
mauve = (0.741, 0.553, 0.773, 1)
black = (0, 0, 0, 1)
white = (1, 1, 1, 1)

# Define the standard contents for each First Aid Box
STANDARD_BOX_CONTENTS = {
    "General First Aid Guidance Card": 1,
    "Assorted Sterile Plasters": 20,
    "Safety Pins": 6,
    "Medium Sterile Dressing (12cm x 12cm)": 6,
    "Large Sterile Dressing (18cm x 18cm)": 2,
    "Sterile Eye Pad Dressing": 2,
    "Sterile Saline Alcohol Free Cleansing Wipe": 6,
    "Nitrile Examination Gloves - Large (Pair)": 4,
    "Non Sterile Non Woven Triangular Bandage": 4,
}

# Load all KV files
KV_FILES = [
    'screens/home.kv',
    'screens/boxcheck.kv',
    'screens/checkhistory.kv',
    'screens/checkdetails.kv'
]

for kv_file in KV_FILES:
    Builder.load_file(kv_file)

# Add this to your main.py file, after the imports and before the existing classes

class ItemCheckCard(MDCard):
    """Custom widget for individual item check cards"""
    
    def __init__(self, item_name, standard_qty, current_qty=0, expiry_date="", item_notes="", **kwargs):
        # Set card properties
        super().__init__(
            orientation="vertical",
            padding="10dp",
            spacing="5dp",
            size_hint_y=None,
            height=dp(180),
            elevation=2,
            radius=[8],
            line_color= sage,
            line_width= 3,
            **kwargs
        )
        
        # Store item data
        self.item_name = item_name
        self.standard_qty = standard_qty
        
        # Create the UI elements
        self.setup_ui(current_qty, expiry_date, item_notes)
    
    def setup_ui(self, current_qty, expiry_date, item_notes):
        """Create and add all UI elements to the card"""
        
        # Item title label
        title_label = MDLabel(
            text=f"{self.item_name} (Std: {self.standard_qty})",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(title_label)
        
        # Input fields container
        inputs_box = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
        )
        
        # Quantity input
        self.qty_input = MDTextField(
            hint_text="Quantity",
            input_filter="int",
            mode="rectangle",
            size_hint_x=0.5,
            max_text_length=3,
            text=str(current_qty) if current_qty > 0 else "",
        )
        inputs_box.add_widget(self.qty_input)
        
        # Expiry date input
        self.expiry_input = MDTextField(
            hint_text="Expiry (YYYY-MM-DD)",
            mode="rectangle",
            size_hint_x=0.5,
            max_text_length=10,
            text=expiry_date or "",
        )
        inputs_box.add_widget(self.expiry_input)
        
        self.add_widget(inputs_box)
        
        # Notes input
        self.notes_input = MDTextField(
            hint_text="Notes for item",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(50),
            text=item_notes or "",
        )
        self.add_widget(self.notes_input)
    
    def get_item_data(self):
        """Get the current data from the card inputs"""
        try:
            current_qty = int(self.qty_input.text) if self.qty_input.text else 0
        except ValueError:
            raise ValueError(f"Quantity for {self.item_name} must be a number!")
        
        expiry_date = self.expiry_input.text
        if expiry_date:
            try:
                datetime.strptime(expiry_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Expiry date for {self.item_name} must be in YYYY-MM-DD format!")
        
        return {
            'item_name': self.item_name,
            'standard_qty': self.standard_qty,
            'current_qty': current_qty,
            'expiry_date': expiry_date,
            'item_notes': self.notes_input.text
        }
    
    def clear_inputs(self):
        """Clear all input fields"""
        self.qty_input.text = ""
        self.expiry_input.text = ""
        self.notes_input.text = ""
        
        
        
        
        

class DatabaseMixin:
    """Mixin class for database operations"""

    @property
    def app(self):
        return MDApp.get_running_app()

    @property
    def cursor(self):
        return self.app.cursor

    @property
    def conn(self):
        return self.app.conn

    def get_first_aid_boxes(self):
        """Returns a list of predefined first aid box names."""
        return ["Back Kitchen", "Cafe", "Upstairs"]

    def get_standard_item_quantity(self, item_name):
        """Get the standard quantity for a given item."""
        return STANDARD_BOX_CONTENTS.get(item_name, 0)

    def format_date_for_display(self, date_str):
        """Format ISO date string for display"""
        if not date_str:
            return ""
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return dt_obj.strftime("%d/%m/%Y")
        except ValueError:
            return date_str


class DialogMixin:
    """Mixin class for dialog operations"""

    def create_confirmation_dialog(self, title, text, confirm_callback):
        """Create a generic confirmation dialog"""
        confirm_dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: confirm_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="CONFIRM",
                    md_bg_color=self.app.theme_cls.primary_color,
                    on_release=lambda x: confirm_callback(confirm_dialog)
                ),
            ],
        )
        confirm_dialog.open()


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "home"


# Replace your existing BoxCheckScreen class with this updated version

class BoxCheckScreen(MDScreen, DatabaseMixin, DialogMixin):
    selected_box = StringProperty("Select First Aid Box")
    current_check_id = None
    
    def on_enter(self):
        self.current_check_id = None
        self.ids.check_date_input.text = datetime.now().strftime("%Y-%m-%d")
        self.ids.notes_input.text = ""
        self.clear_item_inputs()
        self.selected_box = "Select First Aid Box"

    def setup_box_menu(self):
        """Setup the first aid box dropdown menu"""
        box_names = self.get_first_aid_boxes()
        
        box_items = [
            {
                "text": box_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=box_name: self.set_first_aid_box(x),
            }
            for box_name in box_names
        ]
        
        self.box_menu = MDDropdownMenu(
            caller=self.ids.box_selector_card,
            items=box_items,
            position="bottom",
            width_mult=4,
        )

    def open_box_menu(self):
        """Open the first aid box dropdown menu"""
        if not hasattr(self, 'box_menu') or not self.box_menu:
            self.setup_box_menu()
        self.box_menu.open()

    def set_first_aid_box(self, box_name):
        """Set the selected first aid box and load its contents for check."""
        self.selected_box = box_name
        self.box_menu.dismiss()
        self.load_box_contents_for_check()

    def load_box_contents_for_check(self):
        """Load standard contents for the selected box into the form."""
        contents_container = self.ids.contents_container
        contents_container.clear_widgets()

        for item_name, standard_qty in STANDARD_BOX_CONTENTS.items():
            # Create the custom card widget
            card = ItemCheckCard(
                item_name=item_name,
                standard_qty=standard_qty
            )
            contents_container.add_widget(card)

    def clear_item_inputs(self):
        """Clear all item-specific input fields."""
        for card in self.ids.contents_container.children:
            if isinstance(card, ItemCheckCard):
                card.clear_inputs()

    def save_check(self):
        """Save or update the first aid box check."""
        box_name = self.selected_box
        check_date = self.ids.check_date_input.text
        general_notes = self.ids.notes_input.text

        if box_name == "Select First Aid Box":
            toast("Please select a First Aid Box!")
            return
        
        if not check_date:
            check_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            datetime.strptime(check_date, "%Y-%m-%d")
        except ValueError:
            toast("Check Date must be in YYYY-MM-DD format!")
            return

        # Collect item data using the new method
        item_data = []
        try:
            for card in self.ids.contents_container.children:
                if isinstance(card, ItemCheckCard):
                    data = card.get_item_data()
                    item_data.append((
                        data['item_name'],
                        data['standard_qty'],
                        data['current_qty'],
                        data['expiry_date'],
                        data['item_notes']
                    ))
        except ValueError as e:
            toast(str(e))
            return

        try:
            self.conn.execute("BEGIN TRANSACTION;")
            
            if self.current_check_id:
                # Update existing check record
                self.cursor.execute("""
                    UPDATE first_aid_checks
                    SET box_name = ?, check_date = ?, general_notes = ?
                    WHERE id = ?
                """, (box_name, check_date, general_notes, self.current_check_id))
                
                # Delete old item entries and insert new ones for this check
                self.cursor.execute("DELETE FROM check_items WHERE check_id = ?", (self.current_check_id,))
                
            else:
                # Insert new check record
                self.cursor.execute("""
                    INSERT INTO first_aid_checks (box_name, check_date, general_notes)
                    VALUES (?, ?, ?)
                """, (box_name, check_date, general_notes))
                self.current_check_id = self.cursor.lastrowid

            # Insert item details
            for item_name, standard_qty, current_qty, expiry_date, item_notes in item_data:
                self.cursor.execute("""
                    INSERT INTO check_items (check_id, item_name, standard_quantity, current_quantity, expiry_date, item_notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.current_check_id, item_name, standard_qty, current_qty, expiry_date, item_notes))
            
            self.conn.commit()
            toast("First Aid Box check saved successfully!")
            self.app.screen_manager.current = "checkhistory"
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving check: {e}")
            toast("Error saving check. Please try again.")

    def load_check_for_edit(self, check_id):
        """Loads an existing check's data into the input fields for editing"""
        self.current_check_id = check_id
        try:
            self.cursor.execute("""
                SELECT box_name, check_date, general_notes
                FROM first_aid_checks WHERE id = ?
            """, (check_id,))
            check_data = self.cursor.fetchone()

            if check_data:
                box_name, check_date, general_notes = check_data
                self.selected_box = box_name
                self.ids.check_date_input.text = check_date
                self.ids.notes_input.text = general_notes or ""
                self.load_box_contents_for_edit(check_id)
            else:
                toast("Error: Check not found for editing.")
                self.current_check_id = None
        except Exception as e:
            print(f"Error loading check for edit: {e}")
            toast("Error loading check for edit.")
            self.current_check_id = None

    def load_box_contents_for_edit(self, check_id):
        """Load specific item data for editing a check."""
        contents_container = self.ids.contents_container
        contents_container.clear_widgets()

        self.cursor.execute("""
            SELECT item_name, standard_quantity, current_quantity, expiry_date, item_notes
            FROM check_items WHERE check_id = ?
        """, (check_id,))
        item_details = self.cursor.fetchall()

        # Create a dictionary for easy lookup of existing item data
        existing_items = {item[0]: item for item in item_details}

        for item_name, standard_qty in STANDARD_BOX_CONTENTS.items():
            current_qty = 0
            expiry_date = ""
            item_notes = ""

            if item_name in existing_items:
                _, _, current_qty, expiry_date, item_notes = existing_items[item_name]

            # Create the custom card widget with existing data
            card = ItemCheckCard(
                item_name=item_name,
                standard_qty=standard_qty,
                current_qty=current_qty,
                expiry_date=expiry_date,
                item_notes=item_notes
            )
            contents_container.add_widget(card)


class CheckHistoryScreen(MDScreen, DatabaseMixin, DialogMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "checkhistory"
        self.dialog = None

    def on_enter(self):
        self.load_check_history()

    def load_check_history(self):
        """Load all first aid box check records."""
        history_list = self.ids.check_history_list
        history_list.clear_widgets()

        try:
            self.cursor.execute("""
                SELECT id, box_name, check_date, general_notes
                FROM first_aid_checks
                ORDER BY check_date DESC
            """)
            checks_data = self.cursor.fetchall()

            if not checks_data:
                history_list.add_widget(
                    MDLabel(
                        text="No checks recorded yet.",
                        halign="center",
                        valign="center",
                        adaptive_height=True,
                        padding_y="20dp"
                    )
                )
                return

            for check_id, box_name, check_date, general_notes in checks_data:
                date_display = self.format_date_for_display(check_date)
                primary_text = f"{date_display} - {box_name}"
                secondary_text = f"Notes: {general_notes[:50]}..." if general_notes else "No general notes"

                history_list.add_widget(
                    TwoLineListItem(
                        text=primary_text,
                        secondary_text=secondary_text,
                        on_release=lambda x, ch_id=check_id: self.show_check_options(ch_id)
                    )
                )
        except Exception as e:
            print(f"Error loading check history: {e}")
            toast("Error loading check history.")

    def show_check_options(self, check_id):
        """Show options for selected check."""
        self.selected_check_id = check_id
        options = [
            ("View Details", self.view_check_details),
            ("Edit Check", self.edit_check),
            ("Delete Check", self.delete_check_with_confirmation),
        ]
        self.create_options_dialog(f"Check Options", options, check_id)

    def create_options_dialog(self, title, options, selected_id):
        """Create a generic options dialog (overriding DialogMixin to handle dismissal)."""
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
            self.dialog = None
        
        dialog_content = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing="8dp",
            padding="16dp",
        )
        
        for option_text, callback in options:
            dialog_content.add_widget(
                OneLineListItem(
                    text=option_text, 
                    on_release=lambda x, cb=callback: self._execute_option_callback(cb, selected_id)
                )
            )
        
        self.dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=dialog_content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()

    def _execute_option_callback(self, callback, selected_id):
        """Dismiss dialog and then execute the callback."""
        if self.dialog:
            self.dialog.dismiss()
        callback(selected_id)

    def view_check_details(self, check_id):
        """Navigate to check details screen."""
        details_screen = self.app.screen_manager.get_screen('checkdetails')
        details_screen.load_check_details(check_id)
        self.app.screen_manager.current = "checkdetails"

    def edit_check(self, check_id):
        """Navigate to edit check screen."""
        add_reading_screen = self.app.screen_manager.get_screen('boxcheck')
        add_reading_screen.load_check_for_edit(check_id)
        self.app.screen_manager.current = "boxcheck"

    def delete_check_with_confirmation(self, check_id):
        """Delete check with confirmation dialog."""
        self.create_confirmation_dialog(
            "Confirm Delete",
            "Are you sure you want to delete this check record and all its item details?",
            lambda dialog: self._execute_delete_check(check_id, dialog)
        )

    def _execute_delete_check(self, check_id, dialog_to_dismiss):
        """Execute check deletion."""
        dialog_to_dismiss.dismiss()
        try:
            self.conn.execute("BEGIN TRANSACTION;")
            self.cursor.execute("DELETE FROM check_items WHERE check_id = ?", (check_id,))
            self.cursor.execute("DELETE FROM first_aid_checks WHERE id = ?", (check_id,))
            self.conn.commit()
            toast("Check deleted!")
            self.load_check_history() # Reload history after deletion
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting check: {e}")
            toast("Error deleting check.")


class CheckDetailsScreen(MDScreen, DatabaseMixin):
    box_name = StringProperty("")
    check_date_display = StringProperty("")
    general_notes = StringProperty("")
    item_details = ListProperty([]) # List of (item_name, standard_qty, current_qty, expiry_date, item_notes)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "checkdetails"

    def load_check_details(self, check_id):
	    try:
	        self.cursor.execute("""
	            SELECT box_name, check_date, general_notes
	            FROM first_aid_checks WHERE id =?
	        """,(check_id,))
	        check_data = self.cursor.fetchone()
	
	        if check_data:
	            self.box_name, check_date, self.general_notes = check_data
	            self.check_date_display = self.format_date_for_display(check_date)
	            self.general_notes = self.general_notes or "No general notes."
	
	            self.cursor.execute("""
	                SELECT item_name, standard_quantity, current_quantity, expiry_date, item_notes
	                FROM check_items WHERE check_id =?
	                ORDER BY item_name
	            """, (check_id,))
	            self.item_details = self.cursor.fetchall()
	            self.populate_item_details()
	        else:
	            print("No check data found")
	            toast("Error: Check details not found.")
	            self.clear_details()
	    except Exception as e:
	        print(f"Error loading check details: {e}")
	        toast(f"Error loading check details. {e}")
	        self.clear_details()
	













    def populate_item_details(self):
	    """Populate the item details container with cards."""
	    container = self.ids.item_details_container
	    container.clear_widgets()
	
	    if not self.item_details:
	        container.add_widget(
	            MDLabel(
	                text="No item details found for this check.",
	                halign="center",
	                valign="center",
	                adaptive_height=True,
	                padding_y="20dp"
	            )
	        )
	        return
	
	    for item_name, standard_qty, current_qty, expiry_date, item_notes in self.item_details:
	        status_color = self.app.theme_cls.primary_color
	        status_text = "OK"
	
	        if current_qty < standard_qty:
	            status_color = self.app.theme_cls.error_color
	            status_text = "LOW STOCK"
	        elif current_qty > standard_qty:
	            status_text = "OVERSTOCK"
	
	        expiry_status_color = (0, 0, 0, 0)
	        expiry_status_text = ""
	        if expiry_date:
	            try:
	                exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
	                if exp_dt < datetime.now():
	                    expiry_status_color = self.app.theme_cls.error_color
	                    expiry_status_text = "EXPIRED"
	                elif (exp_dt - datetime.now()).days < 90:
	                    expiry_status_color = self.app.theme_cls.accent_color
	                    expiry_status_text = "EXPIRING SOON"
	            except ValueError:
	                pass
	
	        # Create the MDCard
	        card = MDCard(
	            orientation="vertical",
	            padding="0dp",
	            spacing="0dp",
	            size_hint_y=None,
	            height=dp(250 if item_notes else 200),
	            elevation=2,
	            radius=[8],
	        )
	
	        # Header with item name (wrapped and adaptive height)
	
	        
	
	
	        # Main content section
	        content_container = MDBoxLayout(
	            orientation="vertical",
	            padding="15dp",
	            spacing="10dp",
	            size_hint_y=None,
	            height=dp(170 if item_notes else 120)
	        )
	
	        content_container.add_widget(
	            MDLabel(
		            text=f"[b]{item_name}[/b]",
		            font_style="Subtitle1",
		            markup=True,
		            theme_text_color="Custom",
		          
		            
		          
		            text_size=(dp(280), None),
		            size_hint_y=None,
		            adaptive_height=True
		       ) 
	        )
	
	        content_container.add_widget(
	            MDLabel(
	                text=f"Standard Quantity: {standard_qty}",
	                font_style="Body2",
	                size_hint_y=None,
	                height=dp(25)
	            )
	        )
	        content_container.add_widget(
	            MDLabel(
	                text=f"Current Quantity: {current_qty} [color={status_color_to_hex(status_color)}][b]({status_text})[/b][/color]",
	                font_style="Body2",
	                markup=True,
	                size_hint_y=None,
	                height=dp(25)
	            )
	        )
	        content_container.add_widget(
	            MDLabel(
	                text=f"Expiry Date: {self.format_date_for_display(expiry_date)} [color={status_color_to_hex(expiry_status_color)}][b]({expiry_status_text})[/b][/color]" if expiry_date else "Expiry Date: N/A",
	                font_style="Body2",
	                markup=True,
	                size_hint_y=None,
	                height=dp(25)
	            )
	        )
	        content_container.add_widget(
	            MDLabel(
	                text=f"Item Notes: {item_notes if item_notes else 'No notes for this item.'}",
	                font_style="Caption",
	                size_hint_y=None,
	                height=dp(40)
	            )
	        )
	
	        card.add_widget(content_container)
	        container.add_widget(card)
	            
            
            
            
            
            
            
            
            
            

    def clear_details(self):
        """Clear all displayed details."""
        self.box_name = ""
        self.check_date_display = ""
        self.general_notes = ""
        self.item_details = []
        self.ids.item_details_container.clear_widgets()

    def go_back(self):
        """Navigate back to check history screen."""
        self.manager.current = "checkhistory"
        self.manager.transition.direction = 'right'
        self.clear_details()


def status_color_to_hex(color_tuple):
    """Converts an RGBA color tuple to a hex string."""
    if len(color_tuple) == 4:
        r, g, b, _ = color_tuple # Ignore alpha for hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    return "#000000" # Default to black if format is wrong


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber" 

        self.setup_database()
        
        self.screen_manager = MDScreenManager()
        screens = [
            HomeScreen(name="home"),
            BoxCheckScreen(name="boxcheck"),
            CheckHistoryScreen(name="checkhistory"),
            CheckDetailsScreen(name="checkdetails")
        ]
        
        for screen in screens:
            self.screen_manager.add_widget(screen)
        
        self.screen_manager.current = "home"
        return self.screen_manager
    
    def setup_database(self):
        """Initialize database and tables"""
        os.makedirs("database", exist_ok=True)
        
        self.conn = sqlite3.connect("database/first_aid_stock.db")
        self.cursor = self.conn.cursor()
        
        # Create first_aid_checks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS first_aid_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                box_name TEXT NOT NULL,
                check_date TEXT NOT NULL,
                general_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create check_items table to store details for each item in a check
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                standard_quantity INTEGER NOT NULL,
                current_quantity INTEGER NOT NULL,
                expiry_date TEXT,
                item_notes TEXT,
                FOREIGN KEY (check_id) REFERENCES first_aid_checks (id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()
    
    def on_stop(self):
        """Close database connection on app stop"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def callback(self, *args):
        """Handle menu button callback (for general navigation/info)"""
        menu_items = [
            {
                "text": "Perform New Check",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="boxcheck": self.menu_callback(x),
            },
            {
                "text": "View Check History",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="checkhistory": self.menu_callback(x),
            },
            {
                "text": "About",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="About": self.menu_callback(x),
            },
        ]
        
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )
        self.menu.caller = args[0]
        self.menu.open()
    
    def menu_callback(self, text_item):
        """Handle menu item selection"""
        self.menu.dismiss()
        menu_actions = {
            "boxcheck": "boxcheck",
            "checkhistory": "checkhistory",
            "About": self.show_about_dialog,
        }
        
        action = menu_actions.get(text_item)
        if isinstance(action, str):
            self.screen_manager.current = action
        elif callable(action):
            action()
    
    def show_about_dialog(self):
        """Show about dialog"""
        content = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            height="120dp",
            adaptive_height=True
        )
        
        about_text = MDLabel(
            text="First Aid Stock Control App v1.0\n\nManage your first aid box contents and track checks.",
            theme_text_color="Primary",
            halign="left",
            size_hint_y=None,
            height="100dp"
        )
        content.add_widget(about_text)
        
        self.dialog = MDDialog(
            title="About",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
            auto_dismiss=False,
            size_hint=(0.8, None)
        )
        
        self.dialog.open()


if __name__ == "__main__":
    MainApp().run()
