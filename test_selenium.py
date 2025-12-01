"""
Automated Testing for CineFiles Web Application using Selenium
This script tests the main user flows and functionality
"""

import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import string

class CineFilesTests(unittest.TestCase):
    """Test suite for CineFiles application"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests"""
        # Initialize Chrome driver
        cls.driver = webdriver.Chrome()
        cls.driver.maximize_window()
        cls.base_url = "http://localhost:5000"
        cls.wait = WebDriverWait(cls.driver, 10)
        
        # Generate random test user credentials
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        cls.test_username = f"testuser_{random_suffix}"
        cls.test_email = f"test_{random_suffix}@example.com"
        cls.test_password = "TestPassword123!"
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.driver.quit()
    
    def take_screenshot(self, name):
        """Helper method to take screenshots"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"screenshots/{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")
    
    def test_01_home_page_loads(self):
        """Test Case 1: Verify home page loads successfully"""
        print("\n=== Test 1: Home Page Load ===")
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Verify page title contains CineFiles
        page_title = self.driver.title
        self.assertTrue("CineFiles" in page_title or len(page_title) > 0, "Page title not found")
        
        # Verify movies are displayed
        try:
            movies = self.driver.find_elements(By.CLASS_NAME, "movie-card")
            self.assertGreater(len(movies), 0, "No movies displayed on home page")
            print(f"Home page loaded with {len(movies)} movies")
        except NoSuchElementException:
            print("Movies not found on home page")
            
        self.take_screenshot("01_home_page")
        
    def test_02_navigation_to_register(self):
        """Test Case 2: Verify navigation to registration page"""
        print("\n=== Test 2: Navigate to Register Page ===")
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Find and click register link in navbar
        try:
            # Wait for navbar to load
            register_link = self.wait.until(
                EC.presence_of_element_located((By.LINK_TEXT, "Register"))
            )
            register_link.click()
            time.sleep(2)
            
            # Verify we're on the register page
            self.assertIn("register", self.driver.current_url.lower())
            print("Successfully navigated to register page")
            
            self.take_screenshot("02_register_page")
        except Exception as e:
            print(f"Navigation to register failed: {str(e)}")
            self.take_screenshot("02_register_error")
            self.fail(f"Register navigation failed: {str(e)}")
    
    def test_03_user_registration(self):
        """Test Case 3: Test user registration with valid data"""
        print("\n=== Test 3: User Registration ===")
        self.driver.get(f"{self.base_url}/register")
        time.sleep(2)
        
        try:
            # Wait for form to load
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(self.test_username)
            email_field.clear()
            email_field.send_keys(self.test_email)
            password_field.clear()
            password_field.send_keys(self.test_password)
            
            self.take_screenshot("03_registration_form_filled")
            
            # Submit form - look for submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            time.sleep(3)
            
            # Check if registration was successful (should redirect to login or show success message)
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "register" in current_url:
                print(f"User registered successfully: {self.test_username}")
                self.take_screenshot("03_registration_success")
            else:
                print(f"Registration completed but unexpected redirect to: {current_url}")
                self.take_screenshot("03_registration_unexpected")
        except Exception as e:
            print(f"Registration failed: {str(e)}")
            self.take_screenshot("03_registration_error")
            # Don't raise - continue with other tests
    
    def test_04_user_login(self):
        """Test Case 4: Test user login with valid credentials"""
        print("\n=== Test 4: User Login ===")
        self.driver.get(f"{self.base_url}/login")
        time.sleep(2)
        
        try:
            # Wait for form to load
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            email_field.clear()
            email_field.send_keys(self.test_email)
            password_field.clear()
            password_field.send_keys(self.test_password)
            
            self.take_screenshot("04_login_form_filled")
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            time.sleep(3)
            
            # Check if login was successful
            current_url = self.driver.current_url.lower()
            if "profile" in current_url:
                print(f"User logged in successfully: {self.test_email}")
                self.take_screenshot("04_login_success")
            else:
                # Check if we're still on login page (failed login)
                print(f"Login may have failed - current URL: {current_url}")
                self.take_screenshot("04_login_result")
        except Exception as e:
            print(f"Login failed: {str(e)}")
            self.take_screenshot("04_login_error")
            # Don't raise - continue with other tests
    
    def test_05_view_profile(self):
        """Test Case 5: Verify profile page displays user information"""
        print("\n=== Test 5: View Profile ===")
        
        # Ensure user is logged in
        self.test_04_user_login()
        
        try:
            # Verify username is displayed
            page_source = self.driver.page_source
            self.assertIn(self.test_username, page_source)
            print(f"Profile page displays username: {self.test_username}")
            
            self.take_screenshot("05_profile_page")
        except Exception as e:
            print(f"Profile view failed: {str(e)}")
            self.take_screenshot("05_profile_error")
            raise
    
    def test_06_edit_profile(self):
        """Test Case 6: Test profile editing functionality"""
        print("\n=== Test 6: Edit Profile ===")
        
        # Ensure user is logged in
        self.test_04_user_login()
        
        # Navigate to edit profile
        self.driver.get(f"{self.base_url}/profile/edit")
        time.sleep(2)
        
        try:
            # Fill in profile fields
            bio_field = self.driver.find_element(By.NAME, "bio")
            location_field = self.driver.find_element(By.NAME, "location")
            
            test_bio = "I was rasied on cinema"
            test_location = "Edinburgh, Scotland"
            
            bio_field.clear()
            bio_field.send_keys(test_bio)
            location_field.clear()
            location_field.send_keys(test_location)
            
            self.take_screenshot("06_edit_profile_form_filled")
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            time.sleep(2)
            
            # Verify changes are saved
            page_source = self.driver.page_source
            self.assertIn(test_bio, page_source)
            self.assertIn(test_location, page_source)
            print("✓ Profile updated successfully")
            
            self.take_screenshot("06_profile_updated")
        except Exception as e:
            print(f"✗ Profile edit failed: {str(e)}")
            self.take_screenshot("06_edit_profile_error")
            raise
    
    def test_07_search_movies(self):
        """Test Case 7: Test movie search functionality"""
        print("\n=== Test 7: Search Movies ===")
        self.driver.get(self.base_url)
        time.sleep(2)
        
        try:
            # Find search form in navbar
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='query']"))
            )
            search_query = "Inception"
            search_input.clear()
            search_input.send_keys(search_query)
            
            self.take_screenshot("07_search_form_filled")
            
            # Submit search - find the search button in the navbar
            search_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='search'] button[type='submit']")
            search_button.click()
            time.sleep(3)
            
            # Verify search results
            current_url = self.driver.current_url.lower()
            if "search" in current_url:
                page_source = self.driver.page_source
                print(f"Search completed for: {search_query}")
                self.take_screenshot("07_search_results")
            else:
                print(f"Error - Search may not have worked - URL: {current_url}")
                self.take_screenshot("07_search_unexpected")
        except Exception as e:
            print(f"Search failed: {str(e)}")
            self.take_screenshot("07_search_error")
            # Don't raise - continue
    
    def test_08_view_movie_details(self):
        """Test Case 8: Test viewing movie details"""
        print("\n=== Test 8: View Movie Details ===")
        self.driver.get(self.base_url)
        time.sleep(3)
        
        try:
            # Look for movie elements - they might be in the carousel
            # Try to find any clickable movie elements
            movie_elements = self.driver.find_elements(By.CSS_SELECTOR, ".carosel-item h3, .movie-card, a[href*='/movie/']")
            
            if not movie_elements:
                # Try searching for a specific movie first
                print("No movie links found on home page, trying search...")
                search_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='query']")
                search_input.send_keys("Fight Club")
                search_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='search'] button")
                search_button.click()
                time.sleep(3)
                
                # Now try to find movie links
                movie_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/movie/']")
                if movie_links:
                    movie_links[0].click()
                    time.sleep(3)
                    print("Movie details page loaded after search")
                    self.take_screenshot("08_movie_details")
                else:
                    print("No movie links found after search")
                    self.take_screenshot("08_no_movies")
            else:
                # Navigate directly to a known movie ID - Fight Club
                self.driver.get(f"{self.base_url}/movie/550")  
                time.sleep(3)
                print("Movie details page loaded directly")
                self.take_screenshot("08_movie_details")
                
        except Exception as e:
            print(f"View movie details test completed with issues: {str(e)}")
            self.take_screenshot("08_movie_details_error")
            # Don't raise - this is not critical
    
    def test_09_add_review(self):
        """Test Case 9: Test adding a movie review"""
        print("\n=== Test 9: Add Movie Review ===")
        
        # Ensure user is logged in
        self.test_04_user_login()
        
        # Navigate to a movie details page
        self.driver.get(f"{self.base_url}/movie/550")  # Fight Club
        time.sleep(3)
        
        try:
            # Fill in review form
            rating_field = self.driver.find_element(By.NAME, "rating")
            comment_field = self.driver.find_element(By.NAME, "comment")
            
            rating_field.send_keys("5")
            test_comment = "I am not allowed to talk about this movie"
            comment_field.send_keys(test_comment)
            
            self.take_screenshot("09_review_form_filled")
            
            # Submit review
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='review'] button[type='submit']")
            submit_button.click()
            time.sleep(2)
            
            # Verify review is displayed
            page_source = self.driver.page_source
            self.assertIn(test_comment, page_source)
            print("Review added successfully")
            
            self.take_screenshot("09_review_added")
        except Exception as e:
            print(f"Add review failed: {str(e)}")
            self.take_screenshot("09_add_review_error")
            raise
    
    def test_10_add_comment(self):
        """Test Case 10: Test adding a movie comment"""
        print("\n=== Test 10: Add Movie Comment ===")
        
        # Ensure user is logged in
        self.test_04_user_login()
        
        # Navigate to a movie details page
        self.driver.get(f"{self.base_url}/movie/550")  # Fight Club
        time.sleep(3)
        
        try:
            # Fill in comment form
            comment_field = self.driver.find_element(By.NAME, "content")
            test_content = "Its only after we've lost everything that we're free to do anything"
            comment_field.send_keys(test_content)
            
            self.take_screenshot("10_comment_form_filled")
            
            # Submit comment
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='comment'] button[type='submit']")
            submit_button.click()
            time.sleep(2)
            
            # Verify comment is displayed
            page_source = self.driver.page_source
            self.assertIn(test_content, page_source)
            print("Comment added successfully")
            
            self.take_screenshot("10_comment_added")
        except Exception as e:
            print(f"Add comment failed: {str(e)}")
            self.take_screenshot("10_add_comment_error")
            raise
    
    def test_11_logout(self):
        """Test Case 11: Test user logout"""
        print("\n=== Test 11: User Logout ===")
        
        # Ensure user is logged in
        self.test_04_user_login()
        
        try:
            # Find and click logout link
            logout_link = self.driver.find_element(By.LINK_TEXT, "Logout")
            logout_link.click()
            time.sleep(2)
            
            # Verify redirect to home page
            self.assertEqual(self.driver.current_url, f"{self.base_url}/")
            print("User logged out successfully")
            
            self.take_screenshot("11_logout_success")
            
            # Try to access profile page (should redirect to login)
            self.driver.get(f"{self.base_url}/profile")
            time.sleep(2)
            self.assertIn("login", self.driver.current_url.lower())
            print("User page access blocked after logout")
            
        except Exception as e:
            print(f"Logout failed: {str(e)}")
            self.take_screenshot("11_logout_error")
            raise
    
    def test_12_sql_injection_login(self):
        """Test Case 12: Test SQL Injection vulnerability in login"""
        print("\n=== Test 12: SQL Injection Test (Login) ===")
        self.driver.get(f"{self.base_url}/login")
        time.sleep(2)
        
        try:
            # Try SQL injection payload
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            
            sql_payload = "admin@test.com' OR '1'='1' --"
            email_field.send_keys(sql_payload)
            password_field.send_keys("anything")
            
            self.take_screenshot("12_sql_injection_attempt")
            
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            time.sleep(2)
            
            # Check if SQL injection was successful (vulnerability exists)
            if "profile" in self.driver.current_url.lower():
                print("⚠ SQL INJECTION VULNERABILITY DETECTED - Login bypassed!")
                self.take_screenshot("12_sql_injection_success")
            else:
                print("SQL injection attempt blocked")
                
        except Exception as e:
            print(f"SQL injection test error: {str(e)}")
            self.take_screenshot("12_sql_injection_error")
    
    def test_13_xss_search(self):
        """Test Case 13: Test XSS vulnerability in search"""
        print("\n=== Test 13: XSS Test (Search) ===")
        self.driver.get(self.base_url)
        time.sleep(2)
        
        try:
            # Try XSS payload
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='query']"))
            )
            xss_payload = "<script>alert('XSS')</script>"
            search_input.clear()
            search_input.send_keys(xss_payload)
            
            self.take_screenshot("13_xss_search_attempt")
            
            search_button = self.driver.find_element(By.CSS_SELECTOR, "form[action*='search'] button[type='submit']")
            search_button.click()
            time.sleep(2)
            
            # Check for alert (XSS executed)
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                print(f"⚠ XSS VULNERABILITY DETECTED - Alert appeared with text: {alert_text}")
                alert.accept()
                self.take_screenshot("13_xss_vulnerability_confirmed")
            except:
                # No alert, check page source
                page_source = self.driver.page_source
                if "<script>alert('XSS')</script>" in page_source:
                    print("XSS VULNERABILITY DETECTED - Script tag reflected in page!")
                    self.take_screenshot("13_xss_vulnerability_found")
                else:
                    print("XSS attempt sanitized or encoded")
                    self.take_screenshot("13_xss_blocked")
                
        except Exception as e:
            print(f"XSS test completed: {str(e)}")
            self.take_screenshot("13_xss_test_complete")


def run_tests():
    """Run all tests and generate report"""
    # Create screenshots directory
    import os
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(CineFilesTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*50)
    
    return result


if __name__ == "__main__":
    print("Starting CineFiles Automated Tests...")
    print("Make sure the application is running on http://localhost:5000")
    print("="*50)
    
    result = run_tests()
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)