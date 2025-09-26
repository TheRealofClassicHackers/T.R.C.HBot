import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

class WhatsAppClient:
    def __init__(self, user_data_dir="./User_Data"):
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={user_data_dir}")
        self.driver = webdriver.Chrome(options=options)

    def open_whatsapp(self):
        self.driver.get("https://web.whatsapp.com")
        print("Scan QR code if necessary.")
        time.sleep(15)

    def find_contact(self, contact_name):
        try:
            search_box = self.driver.find_element(By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]')
            search_box.clear()
            time.sleep(1)
            search_box.send_keys(contact_name)
            time.sleep(2)
            contact = self.driver.find_element(By.XPATH, f'//span[@title="{contact_name}"]')
            contact.click()
            time.sleep(2)
            return True
        except NoSuchElementException:
            print(f"Contact '{contact_name}' not found.")
            return False

    def send_message(self, text):
        try:
            message_box = self.driver.find_element(By.XPATH, '//div[@contenteditable="true" and @data-tab="10"]')
            message_box.click()
            message_box.send_keys(text + "\n\n")
            message_box.send_keys(Keys.ENTER)
        except Exception as e:
            print("Failed to send message:", e)

    def send_video(self, video_path):
        try:
            attach_btn = self.driver.find_element(By.CSS_SELECTOR, "span[data-icon='clip']")
            attach_btn.click()
            time.sleep(1)
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(video_path)
            time.sleep(3)
            send_btn = self.driver.find_element(By.XPATH,'//span[@data-icon="send"]')
            send_btn.click()
            time.sleep(2)
        except Exception as e:
            print("Failed to send video:", e)

    def send_file(self, file_path):
        try:
            attach_btn = self.driver.find_element(By.CSS_SELECTOR, "span[data-icon='clip']")
            attach_btn.click()
            time.sleep(1)
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(file_path)
            time.sleep(3)
            send_btn = self.driver.find_element(By.XPATH, '//span[@data-icon="send"]')
            send_btn.click()
            time.sleep(2)
        except Exception as e:
            print("Failed to send file:", e)

    def read_last_message(self):
        try:
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div.message-in')
            if not messages:
                return ""
            last_msg = messages[-1].find_element(By.CSS_SELECTOR, "span.selectable-text").text
            return last_msg.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            return ""

    def get_current_chat_name(self):
        try:
            contact_title = self.driver.find_element(By.XPATH, '//header//span[@dir="auto"]')
            return contact_title.text
        except NoSuchElementException:
            return ""
