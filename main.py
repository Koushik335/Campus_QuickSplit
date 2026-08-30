from datetime import datetime
import json
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


# =========================================================
# WINDOW
# =========================================================

Window.size = (430, 860)
Window.minimum_width = 360
Window.minimum_height = 650
Window.clearcolor = (0.965, 0.955, 0.975, 1)


# =========================================================
# COLORS
# =========================================================

BG = (0.965, 0.955, 0.975, 1)
WHITE = (1, 1, 1, 1)

PRIMARY = (0.40, 0.29, 0.58, 1)
PRIMARY_SOFT = (0.91, 0.87, 0.97, 1)

TEXT = (0.11, 0.10, 0.14, 1)
MUTED = (0.49, 0.46, 0.53, 1)

GREEN = (0.16, 0.55, 0.35, 1)
RED = (0.77, 0.25, 0.28, 1)

GREEN_SOFT = (0.90, 0.96, 0.92, 1)
RED_SOFT = (0.98, 0.92, 0.92, 1)


# =========================================================
# HELPERS
# =========================================================

def money(value):
    return f"₹{value:,.2f}"


def short_money(value):
    if abs(value) >= 100000:
        return f"₹{value / 100000:.1f}L"
    if abs(value) >= 1000:
        return f"₹{value / 1000:.1f}K"
    return f"₹{value:,.0f}"


def normalise_name(name):
    name = name.strip()
    if name.lower() == "me":
        return "You"
    return name


def initials(name):
    if name.lower() == "you":
        return "Y"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:1].upper()


def format_time(timestamp):
    now = datetime.now()
    if timestamp.date() == now.date():
        return timestamp.strftime("%I:%M %p")
    return timestamp.strftime("%d %b • %I:%M %p")


def category_symbol(category):
    symbols = {
        "Food": "🍔",
        "Transport": "🚌",
        "Subscriptions": "◉",
        "Printouts": "▤",
        "College": "▣",
        "Other": "•",
    }
    return symbols.get(category, "•")


# =========================================================
# CARD
# =========================================================

class Card(BoxLayout):

    def __init__(self, bg=WHITE, radius=20, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)]
            )
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size


# =========================================================
# UI HELPERS
# =========================================================

def txt(text, size=15, color=TEXT, bold=False, align="left"):
    return Label(
        text=text,
        font_size=dp(size),
        color=color,
        bold=bold,
        halign=align,
        valign="middle"
    )


def button(text, bg=PRIMARY, fg=WHITE, height=48, size=15):
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_color=bg,
        color=fg,
        font_size=dp(size)
    )


def input_box(hint="", height=50, numeric=False):
    return TextInput(
        hint_text=hint,
        multiline=False,
        size_hint_y=None,
        height=dp(height),
        padding=[dp(14), dp(12)],
        background_normal="",
        background_color=(0.98, 0.975, 0.99, 1),
        foreground_color=TEXT,
        cursor_color=PRIMARY,
        font_size=dp(15),
        input_filter="float" if numeric else None
    )


# =========================================================
# EXPENSE MODEL
# =========================================================

class Expense:

    def __init__(self, name, amount, category, paid_by, participants, timestamp=None):
        self.name = name
        self.amount = amount
        self.category = category
        self.paid_by = paid_by
        self.participants = participants
        self.timestamp = timestamp or datetime.now()

    @property
    def share(self):
        if not self.participants:
            return 0.0
        return self.amount / len(self.participants)

    def to_dict(self):
        return {
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "paid_by": self.paid_by,
            "participants": self.participants,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return Expense(
            name=data["name"],
            amount=float(data["amount"]),
            category=data["category"],
            paid_by=data["paid_by"],
            participants=data["participants"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


# =========================================================
# DATA STORE
# =========================================================

class AppData:

    FILE = "quicksplit_data.json"

    def __init__(self):
        self.people = ["You"]
        self.expenses = []
        self.load()

    def add_person(self, name):
        name = normalise_name(name)
        if not name:
            return False
        exists = any(person.lower() == name.lower() for person in self.people)
        if exists:
            return False
        self.people.append(name)
        self.save()
        return True

    def ensure_person(self, name):
        name = normalise_name(name)
        if not name:
            return
        self.add_person(name)

    def parse_participants(self, text):
        if not text.strip():
            return []
        result = []
        for raw in text.split(","):
            person = normalise_name(raw)
            if not person:
                continue
            duplicate = any(existing.lower() == person.lower() for existing in result)
            if not duplicate:
                result.append(person)
        return result

    def add_expense(self, name, amount, category, paid_by, participants):
        self.ensure_person(paid_by)
        for person in participants:
            self.ensure_person(person)
        self.expenses.insert(0, Expense(
            name=name,
            amount=amount,
            category=category,
            paid_by=paid_by,
            participants=participants
        ))
        self.save()

    def delete_expense(self, expense):
        if expense in self.expenses:
            self.expenses.remove(expense)
            self.save()

    def total_spending(self):
        return sum(expense.amount for expense in self.expenses)

    def total_paid(self, person):
        return sum(expense.amount for expense in self.expenses if expense.paid_by == person)

    def balance_for(self, person):
        balance = 0.0
        for expense in self.expenses:
            if expense.paid_by == person:
                balance += expense.amount
            if person in expense.participants:
                balance -= expense.share
        return round(balance, 2)

    def balances(self):
        return {person: self.balance_for(person) for person in self.people}

    def save(self):
        data = {
            "people": self.people,
            "expenses": [expense.to_dict() for expense in self.expenses]
        }
        try:
            with open(self.FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        except Exception as error:
            print("Save error:", error)

    def load(self):
        if not os.path.exists(self.FILE):
            return
        try:
            with open(self.FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.people = data.get("people", ["You"])
            self.expenses = [Expense.from_dict(item) for item in data.get("expenses", [])]
            if "You" not in self.people:
                self.people.insert(0, "You")
        except Exception as error:
            print("Load error:", error)


# =========================================================
# DASHBOARD
# =========================================================

class Dashboard(Screen):

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")
        scroll = ScrollView(do_scroll_x=False)

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(20), dp(20), dp(25)],
            spacing=dp(13),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter("height"))

        # HEADER
        header = BoxLayout(size_hint_y=None, height=dp(70))
        title_box = BoxLayout(orientation="vertical")
        title_box.add_widget(txt("CAMPUS", 11, PRIMARY, True))
        title_box.add_widget(txt("QuickSplit", 29, TEXT, True))
        title_box.add_widget(txt("Shared expenses, minus the awkward math.", 12, MUTED))
        header.add_widget(title_box)

        wallet = Card(orientation="vertical", bg=PRIMARY_SOFT, radius=17)
        wallet.size_hint_x = None
        wallet.width = dp(48)
        wallet.add_widget(txt("₹", 22, PRIMARY, True, "center"))
        header.add_widget(wallet)
        content.add_widget(header)

        # BALANCE HERO
        balance = self.data.balance_for("You")
        if balance > 0.01:
            eyebrow, value, message = "YOU SHOULD RECEIVE", money(balance), "Your group owes you."
        elif balance < -0.01:
            eyebrow, value, message = "YOU OWE", money(abs(balance)), "Your pending group share."
        else:
            eyebrow, value, message = "ALL SETTLED", "₹0.00", "Nothing is pending right now."

        hero = Card(orientation="vertical", padding=dp(22), spacing=dp(3), bg=PRIMARY, radius=28)
        hero.size_hint_y = None
        hero.height = dp(165)
        hero.add_widget(txt(eyebrow, 10, (0.90, 0.87, 0.97, 1), True))
        hero.add_widget(txt(value, 39, WHITE, True))
        hero.add_widget(txt(message, 13, (0.90, 0.87, 0.97, 1)))
        content.add_widget(hero)

        # STATS
        stats = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(100))
        stats.add_widget(self.stat_card("GROUP SPENDING", short_money(self.data.total_spending()), "all shared costs"))
        stats.add_widget(self.stat_card("YOU PAID", short_money(self.data.total_paid("You")), "money advanced"))
        content.add_widget(stats)

        # PEOPLE
        title_row = BoxLayout(size_hint_y=None, height=dp(32))
        title_row.add_widget(txt("People", 20, TEXT, True))
        add_person = button("+ Add", PRIMARY_SOFT, PRIMARY, 32, 12)
        add_person.size_hint_x = None
        add_person.width = dp(70)
        add_person.bind(on_release=lambda *_: self.open_people())
        title_row.add_widget(add_person)
        content.add_widget(title_row)

        people_scroll = ScrollView(size_hint_y=None, height=dp(85), do_scroll_y=False)
        people_row = BoxLayout(spacing=dp(9), size_hint_x=None)
        people_row.bind(minimum_width=people_row.setter("width"))
        for person in self.data.people:
            people_row.add_widget(self.person_chip(person))
        people_scroll.add_widget(people_row)
        content.add_widget(people_scroll)

        # BALANCES
        content.add_widget(txt("Balances", 20, TEXT, True))
        for person in self.data.people:
            content.add_widget(self.balance_row(person))

        # ACTIVITY
        content.add_widget(txt("Recent activity", 20, TEXT, True))
        if not self.data.expenses:
            empty = Card(orientation="vertical", padding=dp(17))
            empty.size_hint_y = None
            empty.height = dp(82)
            empty.add_widget(txt("No expenses yet.", 15, TEXT, True))
            empty.add_widget(txt("Your first expense will appear here.", 12, MUTED))
            content.add_widget(empty)
        else:
            for expense in self.data.expenses[:5]:
                content.add_widget(self.activity_row(expense))

        scroll.add_widget(content)
        root.add_widget(scroll)

        add_expense = button("+   Add expense", PRIMARY, WHITE, 55, 16)
        add_expense.bind(on_release=lambda *_: self.open_expense())
        root.add_widget(add_expense)
        self.add_widget(root)

    def stat_card(self, title, value, subtitle):
        card = Card(orientation="vertical", padding=dp(16), spacing=dp(1))
        card.add_widget(txt(title, 9, MUTED, True))
        card.add_widget(txt(value, 22, TEXT, True))
        card.add_widget(txt(subtitle, 10, MUTED))
        return card

    def person_chip(self, person):
        card = Card(orientation="vertical", bg=WHITE, radius=18)
        card.size_hint_x, card.width = None, dp(74)
        card.size_hint_y, card.height = None, dp(80)

        avatar = Card(orientation="vertical", bg=PRIMARY_SOFT, radius=24)
        avatar.size_hint_y, avatar.height = None, dp(38)
        avatar.add_widget(txt(initials(person), 13, PRIMARY, True, "center"))

        card.add_widget(avatar)
        card.add_widget(txt(person, 11, TEXT, True, "center"))
        return card

    def balance_row(self, person):
        balance = self.data.balance_for(person)
        if balance > 0.01:
            status, status_color = f"Gets {money(balance)}", GREEN
        elif balance < -0.01:
            status, status_color = f"Owes {money(abs(balance))}", RED
        else:
            status, status_color = "Settled", MUTED

        row = Card(orientation="horizontal", padding=[dp(13), dp(7)], spacing=dp(10))
        row.size_hint_y, row.height = None, dp(60)

        avatar = Card(orientation="vertical", bg=PRIMARY_SOFT, radius=25)
        avatar.size_hint_x, avatar.width = None, dp(42)
        avatar.add_widget(txt(initials(person), 13, PRIMARY, True, "center"))
        row.add_widget(avatar)

        info = BoxLayout(orientation="vertical")
        info.add_widget(txt(person, 14, TEXT, True))
        info.add_widget(txt("Group member", 10, MUTED))
        row.add_widget(info)
        row.add_widget(txt(status, 12, status_color, True, "right"))
        return row

    def activity_row(self, expense):
        row = Card(orientation="horizontal", padding=[dp(12), dp(7)], spacing=dp(10))
        row.size_hint_y, row.height = None, dp(73)

        badge = Card(orientation="vertical", bg=PRIMARY_SOFT, radius=14)
        badge.size_hint_x, badge.width = None, dp(45)
        badge.add_widget(txt(category_symbol(expense.category), 18, PRIMARY, False, "center"))
        row.add_widget(badge)

        details = BoxLayout(orientation="vertical")
        details.add_widget(txt(expense.name, 14, TEXT, True))
        details.add_widget(txt(f"{expense.paid_by} paid • {len(expense.participants)} sharing", 11, MUTED))
        details.add_widget(txt(f"{money(expense.share)} each • {format_time(expense.timestamp)}", 10, MUTED))
        row.add_widget(details)
        row.add_widget(txt(money(expense.amount), 14, TEXT, True, "right"))
        return row

    def open_people(self):
        screen = PeopleScreen(self.data, self)
        screen.name = "people"
        self.manager.add_widget(screen)
        self.manager.current = "people"

    def open_expense(self):
        screen = ExpenseScreen(self.data, self)
        screen.name = "expense"
        self.manager.add_widget(screen)
        self.manager.current = "expense"


# =========================================================
# PEOPLE SCREEN
# =========================================================

class PeopleScreen(Screen):

    def __init__(self, data, dashboard, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.dashboard = dashboard
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))

        header = BoxLayout(size_hint_y=None, height=dp(55))
        back = button("‹", (0, 0, 0, 0), PRIMARY, 48, 30)
        back.size_hint_x, back.width = None, dp(46)
        back.bind(on_release=lambda *_: self.go_back())
        header.add_widget(back)
        header.add_widget(txt("People", 27, TEXT, True))
        root.add_widget(header)

        root.add_widget(txt("Everyone here can be selected as a payer.", 13, MUTED))

        add_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        name_input = input_box("Add someone...")
        add_row.add_widget(name_input)
        add = button("+", PRIMARY, WHITE, 50, 20)
        add.size_hint_x, add.width = None, dp(55)
        add_row.add_widget(add)
        root.add_widget(add_row)

        scroll = ScrollView()
        people_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        people_box.bind(minimum_height=people_box.setter("height"))

        def refresh():
            people_box.clear_widgets()
            for person in self.data.people:
                balance = self.data.balance_for(person)
                row = Card(orientation="horizontal", padding=[dp(13), dp(7)], spacing=dp(10))
                row.size_hint_y, row.height = None, dp(61)

                avatar = Card(orientation="vertical", bg=PRIMARY_SOFT, radius=25)
                avatar.size_hint_x, avatar.width = None, dp(42)
                avatar.add_widget(txt(initials(person), 13, PRIMARY, True, "center"))
                row.add_widget(avatar)

                info = BoxLayout(orientation="vertical")
                info.add_widget(txt(person, 14, TEXT, True))
                info.add_widget(txt("You" if person == "You" else "Group member", 10, MUTED))
                row.add_widget(info)

                row.add_widget(txt(
                    "Settled" if abs(balance) < 0.01 else money(abs(balance)),
                    12, GREEN if balance >= 0 else RED, True, "right"
                ))
                people_box.add_widget(row)

        refresh()
        scroll.add_widget(people_box)
        root.add_widget(scroll)

        done = button("Done", PRIMARY)
        done.bind(on_release=lambda *_: self.go_back())
        root.add_widget(done)

        def add_person(_):
            name = name_input.text.strip()
            if self.data.add_person(name):
                name_input.text = ""
                refresh()

        add.bind(on_release=add_person)
        self.add_widget(root)

    def go_back(self):
        self.dashboard.build()
        self.manager.current = "dashboard"
        self.manager.remove_widget(self)


# =========================================================
# EXPENSE SCREEN
# =========================================================

class ExpenseScreen(Screen):

    def __init__(self, data, dashboard, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.dashboard = dashboard
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(15), dp(18), dp(18)], spacing=dp(10))

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------
        header = BoxLayout(size_hint_y=None, height=dp(55))
        back = button("‹", (0, 0, 0, 0), PRIMARY, 48, 30)
        back.size_hint_x, back.width = None, dp(46)
        back.bind(on_release=lambda *_: self.go_back())
        header.add_widget(back)
        header.add_widget(txt("Add expense", 26, TEXT, True))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=dp(11), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # -------------------------------------------------
        # 1. DETAILS
        # -------------------------------------------------
        details = Card(orientation="vertical", padding=dp(16), spacing=dp(9))
        details.add_widget(txt("DETAILS", 10, PRIMARY, True))

        self.name_input = input_box("Expense name  •  e.g. Dinner")
        details.add_widget(self.name_input)

        self.amount_input = input_box("Amount  •  ₹0.00", numeric=True)
        details.add_widget(self.amount_input)

        self.category_input = input_box("Category  •  Food")
        self.category_input.text = "Food"
        details.add_widget(self.category_input)
        content.add_widget(details)

        # -------------------------------------------------
        # 2. PARTICIPANTS (Comma-separated input)
        # THIS IS NOW PLACED FIRST
        # -------------------------------------------------
        participant_card = Card(orientation="vertical", padding=dp(16), spacing=dp(8))
        participant_card.add_widget(txt("WHO SHARES IT?", 10, PRIMARY, True))
        participant_card.add_widget(txt("Enter comma-separated names (e.g. ME, Rahul, Arjun)", 11, MUTED))

        self.manual_input = input_box("Rahul, Arjun, ME")
        participant_card.add_widget(self.manual_input)
        participant_card.add_widget(txt("ME means You. You are never added automatically.", 11, MUTED))
        content.add_widget(participant_card)

        # -------------------------------------------------
        # 3. WHO PAID (Dropdown derived dynamically from above)
        # THIS IS NOW PLACED AFTER PARTICIPANTS
        # -------------------------------------------------
        payer_card = Card(orientation="vertical", padding=dp(16), spacing=dp(8))
        payer_card.add_widget(txt("WHO PAID?", 10, PRIMARY, True))
        payer_card.add_widget(txt("Select the person who paid from the participants.", 11, MUTED))

        self.paid_by = Spinner(
            text="Select payer",
            values=[],  # Initializes empty, updates dynamically
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=WHITE,
            color=TEXT,
            font_size=dp(15)
        )
        payer_card.add_widget(self.paid_by)
        content.add_widget(payer_card)

        # -------------------------------------------------
        # 4. SPLIT PREVIEW
        # -------------------------------------------------
        preview = Card(orientation="vertical", padding=dp(16), spacing=dp(4), bg=PRIMARY_SOFT, radius=18)
        preview.add_widget(txt("SPLIT PREVIEW", 10, PRIMARY, True))
        self.preview_label = txt("0 participants  •  ₹0.00 each", 18, TEXT, True)
        preview.add_widget(self.preview_label)
        content.add_widget(preview)

        scroll.add_widget(content)
        root.add_widget(scroll)

        # -------------------------------------------------
        # SAVE BUTTON
        # -------------------------------------------------
        save = button("Save expense   →", PRIMARY, WHITE, 55, 16)
        save.bind(on_release=lambda *_: self.save_expense())
        root.add_widget(save)

        self.add_widget(root)

        # Bind inputs for real-time synchronization
        self.manual_input.bind(text=self.update_preview)
        self.amount_input.bind(text=self.update_preview)
        self.update_preview()

    # =====================================================
    # PREVIEW + PAYER UPDATE (LIVE SYNC)
    # =====================================================
    def update_preview(self, *_):
        try:
            amount = float(self.amount_input.text.strip())
        except ValueError:
            amount = 0.0

        # Parse participants directly from input field
        people = self.data.parse_participants(self.manual_input.text)

        # Force cast to list for Kivy's values property safety
        self.paid_by.values = list(people)

        # If the currently selected payer is no longer a valid participant, reset it
        if self.paid_by.text not in people:
            if people:
                self.paid_by.text = people[0]
            else:
                self.paid_by.text = "Select payer"

        # Update preview label calculations
        if not people:
            self.preview_label.text = "0 participants  •  ₹0.00 each"
        else:
            share = amount / len(people) if amount > 0 else 0.0
            plural = "s" if len(people) != 1 else ""
            self.preview_label.text = f"{len(people)} participant{plural}  •  {money(share)} each"

    # =====================================================
    # SAVE EXPENSE
    # =====================================================
    def save_expense(self):
        name = self.name_input.text.strip()
        if not name:
            self.error("Give the expense a name.")
            return

        try:
            amount = float(self.amount_input.text.strip())
        except ValueError:
            amount = 0.0

        if amount <= 0:
            self.error("Enter a positive amount.")
            return

        participants = self.data.parse_participants(self.manual_input.text)
        if not participants:
            self.error("Provide at least one participant.\n\nType ME if you want yourself included.")
            return

        payer = self.paid_by.text.strip()
        if payer == "Select payer" or not payer:
            self.error("Select who paid.")
            return

        if payer not in participants:
            self.error("The payer must be one of the participants.")
            return

        for person in participants:
            self.data.ensure_person(person)
        self.data.ensure_person(payer)

        self.data.add_expense(
            name=name,
            amount=amount,
            category=(self.category_input.text.strip() or "Other"),
            paid_by=payer,
            participants=participants
        )

        self.dashboard.build()
        self.manager.current = "dashboard"
        self.manager.remove_widget(self)

    # =====================================================
    # ERROR MODAL
    # =====================================================
    def error(self, message):
        popup = ModalView(size_hint=(0.84, 0.34), background_color=(0, 0, 0, 0.30))
        box = Card(orientation="vertical", padding=dp(18), spacing=dp(12))
        box.add_widget(txt("Check that", 20, TEXT, True))
        box.add_widget(txt(message, 13, MUTED))

        okay = button("Okay", PRIMARY, WHITE, 44, 14)
        okay.bind(on_release=popup.dismiss)
        box.add_widget(okay)

        popup.add_widget(box)
        popup.open()

    def go_back(self):
        self.manager.current = "dashboard"
        self.manager.remove_widget(self)


# =========================================================
# APP
# =========================================================

class QuickSplitApp(App):
    def build(self):
        self.title = "Campus QuickSplit"
        data = AppData()
        manager = ScreenManager()
        dashboard = Dashboard(data, name="dashboard")
        manager.add_widget(dashboard)
        return manager


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    QuickSplitApp().run()