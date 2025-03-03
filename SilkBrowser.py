import sys
import socket
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineCore import *
import os
import urllib.request

class SilkBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Check for internet connection at the start
        if not self.check_internet_connection():
            self.show_no_internet_error()
            sys.exit(1)

        # Set the title of the window
        self.setWindowTitle("Silk Browser")

        # Set the size of the window
        self.resize(1280, 720)

        # Set the application icon (SilkBrowser.ico)
        self.setWindowIcon(QIcon("SilkBrowser.ico"))

        # Create a tab widget to manage multiple tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarClicked.connect(self.tab_changed)

        # Set the tab widget as the central widget
        self.setCentralWidget(self.tabs)

        # Create a toolbar for navigation
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        # Add New Tab button with a plus icon
        self.new_tab_btn = QAction(QIcon.fromTheme("document-new"), 'New Tab', self)
        self.new_tab_btn.triggered.connect(self.new_tab)
        self.navbar.addAction(self.new_tab_btn)

        # Add a back button
        self.back_btn = QAction('Back', self)
        self.back_btn.triggered.connect(self.back)
        self.navbar.addAction(self.back_btn)

        # Add a forward button
        self.forward_btn = QAction('Forward', self)
        self.forward_btn.triggered.connect(self.forward)
        self.navbar.addAction(self.forward_btn)

        # Add Reload button
        self.reload_btn = QAction('Reload', self)
        self.reload_btn.triggered.connect(self.reload)
        self.navbar.addAction(self.reload_btn)

        # Add an address bar
        self.url_bar = QLineEdit(self)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        # Add a Menu Bar with Settings
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")

        # History Action
        self.history_action = QAction("Show History", self)
        self.history_action.triggered.connect(self.show_history)
        settings_menu.addAction(self.history_action)

        # Start with one tab (blank page)
        self.new_tab()

        # Set the default light mode style
        self.set_default_style()

        # Initialize history list
        self.history = []

    def new_tab(self):
        # Create a new browser tab with an empty about:blank page
        browser = CustomWebEngineView()
        browser.setUrl(QUrl("about:blank"))

        # Create a QWidget for the tab and add the browser to it
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(browser)
        tab.setLayout(tab_layout)

        # Add the new tab to the tab widget
        tab_index = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(tab_index)

        # Connect the URL change to update the address bar and track history
        browser.urlChanged.connect(self.update_url_bar)
        browser.urlChanged.connect(self.track_history)

        # Intercept download requests
        browser.page().profile().downloadRequested.connect(self.on_download_requested)

    def on_download_requested(self, download_item):
        """Handle download requests and ask for confirmation."""
        # Create a confirmation dialog
        reply = QMessageBox.warning(self, "Download Confirmation",
                                     f"Are you sure you want to download this file? {download_item.url().fileName()}",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Show a file dialog to choose where to save the file
            save_path, _ = QFileDialog.getSaveFileName(self, "Save File", download_item.url().fileName())
            if save_path:
                # Set the download destination and start the download
                download_item.setPath(save_path)
                download_item.accept()  # Accept the download
        else:
            download_item.cancel()  # Cancel the download

    def back(self):
        current_browser = self.current_browser()
        if current_browser:
            current_browser.back()

    def forward(self):
        current_browser = self.current_browser()
        if current_browser:
            current_browser.forward()

    def reload(self):
        current_browser = self.current_browser()
        if current_browser:
            current_browser.reload()

    def navigate_to_url(self):
        url = self.url_bar.text()
        if url:
            # Properly format URL if not already in correct format (e.g., missing "http://")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url
            current_browser = self.current_browser()
            if current_browser:
                current_browser.setUrl(QUrl(url))

    def current_browser(self):
        # Get the current active browser in the selected tab
        return self.tabs.currentWidget().findChild(QWebEngineView)

    def update_url_bar(self, qurl):
        # Update the URL bar with the current URL
        self.url_bar.setText(qurl.toString())

    def tab_changed(self):
        # Update the address bar when switching tabs
        current_browser = self.current_browser()
        if current_browser:
            self.url_bar.setText(current_browser.url().toString())

    def set_default_style(self):
        # Set the default light mode style for the browser
        self.setStyleSheet("""
            QToolBar {
                background-color: #f0f0f0;
                color: black;
            }
            QToolBar QLineEdit {
                background-color: white;
                color: black;
            }
            QWidget {
                background-color: white;
                color: black;
            }
            QTabWidget::pane {
                background: white;
            }
            QTabWidget::tab-bar {
                background: white;
            }
            QTabWidget::tab {
                background-color: #f0f0f0;
                color: black;
            }
            QTabWidget::tab:selected {
                background-color: #dcdcdc;
            }
        """)

    def track_history(self, qurl):
        # Track the history of visited URLs
        if qurl.toString() not in self.history:
            self.history.append(qurl.toString())

    def show_history(self):
        # Show the browsing history in a dialog
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("Browsing History")
        history_layout = QVBoxLayout()

        # Create a list widget to display the history
        history_list = QListWidget(history_dialog)
        history_list.addItems(self.history)
        history_layout.addWidget(history_list)

        history_dialog.setLayout(history_layout)
        history_dialog.exec_()

    def check_internet_connection(self):
        """Check if the system has an active internet connection."""
        try:
            # Try to connect to a reliable host like Google DNS (8.8.8.8)
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

    def show_no_internet_error(self):
        """Show a message box when no internet connection is detected."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("You are not connected to the internet. The internet is required to use Silk Browser. Silk will now exit.")
        msg.setWindowTitle("No Internet Connection")
        msg.exec_()


class CustomWebEngineView(QWebEngineView):
    def __init__(self):
        super().__init__()

    def contextMenuEvent(self, event):
        # Create a custom context menu
        context_menu = QMenu(self)

        # Add custom actions to the menu
        save_as_action = context_menu.addAction("Save As...")
        save_as_action.triggered.connect(self.save_as)

        # Add the default context menu items (if any)
        context_menu.addSeparator()
        default_actions = self.page().actions()
        for action in default_actions:
            context_menu.addAction(action)

        # Show the context menu at the position of the right-click
        context_menu.exec_(event.globalPos())

    def save_as(self):
        # Prompt the user for a location to save the current page as HTML
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "HTML Files (*.html);;All Files (*)")
        if file_path:
            # Save the page content to the specified location
            url = self.url().toString()
            page = self.page()
            page.toHtml(self.save_page_to_file(file_path))

    def save_page_to_file(self, file_path):
        """Function to save the current page to the specified file."""
        def save_callback(html):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)

        return save_callback


def main():
    app = QApplication(sys.argv)

    # Set Application Style
    app.setApplicationName("Silk Browser")

    # Create the main window
    window = SilkBrowser()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
