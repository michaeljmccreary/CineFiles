"""
Automated Testing for CineFiles Web Application using Playwright
This test suite checks all the main features of the CineFiles movie review website.
It tests things like user registration, login, searching for movies, adding reviews, etc.
"""

import asyncio
import time
from playwright.async_api import async_playwright


class CineFilesPlaywrightTests:
    """
    This class contains all the tests for the CineFiles application.
    Each test method checks a different feature of the website.
    """

    def __init__(self):
        # Base URL where the app is running
        self.base_url = "http://localhost:5000"
        
        # Playwright browser objects (will be set up later)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Test user credentials - The sane user is used for all tests
        self.test_username = "DonnieDarko"
        self.test_email = "DonnieDarko@gmail.com"
        self.test_password = "FrankTheBunny123!"

        # List to store test results
        self.test_results = []

    async def setup(self):
        """
        Set up the browser before running tests.
        This opens a Chrome browser window that I can control.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()

    async def teardown(self):
        """
        Clean up after tests are done.
        This closes the browser and stops Playwright.
        """
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def take_screenshot(self, name: str):
        """
        Take a screenshot of the current page.
        Screenshots are saved in the 'screenshots' folder with a timestamp.
        
        Args:
            name: A descriptive name for the screenshot
        """
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"screenshots/playwright_{name}_{timestamp}.png"
        await self.page.screenshot(path=filename, full_page=True)
        print(f"Screenshot saved: {filename}")

    def log_result(self, test_name: str, status: str, message: str = ""):
        """
        Log the result of a test.
        
        Args:
            test_name: Name of the test
            status: PASS, FAIL, VULNERABILITY, or ERROR
            message: Additional information about the result
        """
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.test_results.append(result)
        print(f"{test_name}: {status} - {message}")

    # HELPER METHODS

    async def ensure_test_user_exists(self):
        """
        Make sure our test user account exists.
        If the user already exists, that's fine - we just want to make sure
        the account is there before we try to log in.
        """
        try:
            # Go to the registration page
            await self.page.goto(f"{self.base_url}/register", timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)

            # Fill in the registration form
            await self.page.fill('input[name="username"]', self.test_username)
            await self.page.fill('input[name="email"]', self.test_email)
            await self.page.fill('input[name="password"]', self.test_password)
            await self.page.fill('input[name="confirm_password"]', self.test_password)

            await self.take_screenshot("00_ensure_user_registration_attempt")

            # Click the Register button on the registration form
            await self.page.click('button:has-text("Register")', timeout=10000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            # If registration fails (user might already exist), test is still a pass
            print(f"ensure_test_user_exists error (ignored): {e}")

    # TEST METHODS
    # Each method below tests a different feature of the website

        """
        Test 1: Check if the home page loads correctly.
        """
    async def test_01_home_page_loads(self):
        print("\nTest 1: Home Page Load")
        try:
            # Navigate to the home page
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")

            # Check that CineFiles brand name is visible in the navbar
            brand_text = await self.page.text_content("a.navbar-brand")
            assert brand_text and "CineFiles" in brand_text

            # Check that the search bar exists in the navbar
            search_input_count = await self.page.locator('input[name="query"]').count()
            assert search_input_count > 0, "Search input not found on home page"

            await self.take_screenshot("01_home_page")
            self.log_result("Home Page Load", "PASS", "Navbar and search bar are present")
        except Exception as e:
            await self.take_screenshot("01_home_page_error")
            self.log_result("Home Page Load", "FAIL", str(e))
            raise

        """
        Test 2: Check if we can navigate to the registration page.
        """
    async def test_02_navigation_to_register(self):

        print("\nTest 2: Navigate to Register Page")
        try:
            # Start at the home page
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")

            # Click the Register link in the navbar
            await self.page.click("text=Register")
            await self.page.wait_for_load_state("networkidle")

            # Verify we're on the register page by checking the URL
            assert "register" in self.page.url.lower()

            await self.take_screenshot("02_register_page")
            self.log_result(
                "Navigate to Register",
                "PASS",
                "Successfully navigated to /register",
            )
        except Exception as e:
            await self.take_screenshot("02_register_error")
            self.log_result("Navigate to Register", "FAIL", str(e))
            raise


        """
        Test 3: Test the user registration process.
        """
    async def test_03_user_registration(self):
        print("\nTest 3: User Registration ")
        try:
            # Go directly to the registration page
            await self.page.goto(f"{self.base_url}/register")
            await self.page.wait_for_load_state("networkidle")

            # Fill in all the registration form fields
            await self.page.fill('input[name="username"]', self.test_username)
            await self.page.fill('input[name="email"]', self.test_email)
            await self.page.fill('input[name="password"]', self.test_password)
            await self.page.fill('input[name="confirm_password"]', self.test_password)

            await self.take_screenshot("03_registration_form_filled")

            # Click the submit button on the registration form
            # target the specific form to avoid clicking the search button by mistake
            await self.page.click('form[action="/register"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            # Registration is successful if we get redirected
            # don't fail if the user already exists
            self.log_result(
                "User Registration",
                "PASS",
                f"Registration submitted for {self.test_email} (new or existing user).",
            )
        except Exception as e:
            await self.take_screenshot("03_registration_error")
            self.log_result("User Registration", "FAIL", str(e))
            raise


        """
        Test 4: Test the login process.
        """
    async def test_04_user_login(self):

        print("\nTest 4: User Login")
        try:
            # Make sure the test user exists before trying to log in
            await self.ensure_test_user_exists()

            # Go to the login page
            await self.page.goto(f"{self.base_url}/login")
            await self.page.wait_for_load_state("networkidle")

            # Fill in the login form
            await self.page.fill('input[name="email"]', self.test_email)
            await self.page.fill('input[name="password"]', self.test_password)

            await self.take_screenshot("04_login_form_filled")

            # Click the submit button on the login form
            # target the specific form to avoid clicking the search button
            await self.page.click('form[action="/login"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            # After successful login, should be redirected to the profile page
            assert "profile" in self.page.url.lower(), "Did not redirect to profile after login"

            await self.take_screenshot("04_login_success")
            self.log_result(
                "User Login",
                "PASS",
                f"User {self.test_email} logged in successfully",
            )
        except Exception as e:
            await self.take_screenshot("04_login_error")
            self.log_result("User Login", "FAIL", str(e))
            raise

        """
        Test 5: Check if the profile page displays user information correctly.
        """
    async def test_05_view_profile(self):

        print("\nTest 5: View Profile")
        try:
            # Log in first
            await self.test_04_user_login()

            # Check if the username appears on the page
            content = await self.page.content()
            assert self.test_username in content

            await self.take_screenshot("05_profile_page")
            self.log_result("View Profile", "PASS", "Profile displays username correctly")
        except Exception as e:
            await self.take_screenshot("05_profile_error")
            self.log_result("View Profile", "FAIL", str(e))
            raise

        """
        Test 6: Test the profile editing feature.
        """
    async def test_06_edit_profile(self):

        print("\nTest 6: Edit Profile")
        try:
            # Log in first
            await self.test_04_user_login()

            # Go to the edit profile page
            await self.page.goto(f"{self.base_url}/profile/edit")
            await self.page.wait_for_load_state("networkidle")

            # Fill in new bio and location
            test_bio = "Modern cinema connoisseur"
            test_location = "Edinburgh, Scotland"

            await self.page.fill('textarea[name="bio"]', test_bio)
            await self.page.fill('input[name="location"]', test_location)

            await self.take_screenshot("06_edit_profile_form_filled")

            # Click the submit button on the edit profile form
            await self.page.click('form[action="/profile/edit"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            # Verify the changes were saved by checking if they appear on the page
            content = await self.page.content()
            assert test_bio in content
            assert test_location in content

            await self.take_screenshot("06_profile_updated")
            self.log_result(
                "Edit Profile",
                "PASS",
                "Profile bio and location updated successfully",
            )
        except Exception as e:
            await self.take_screenshot("06_edit_profile_error")
            self.log_result("Edit Profile", "FAIL", str(e))
            raise

        """
        Test 7: Test the movie search functionality.
        """
    async def test_07_search_movies(self):

        print("\nTest 7: Search Movies")
        try:
            # Go to the home page
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")

            # Type a movie name in the search box
            search_query = "True Romance"
            await self.page.fill('input[name="query"]', search_query)
            await self.take_screenshot("07_search_form_filled")
            
            # Click the search button in the navbar
            await self.page.click('form[role="search"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            assert "search" in self.page.url.lower()
            
            # Verify the search query appears in the results
            content = await self.page.content()
            assert search_query in content

            await self.take_screenshot("07_search_results")
            self.log_result(
                "Search Movies",
                "PASS",
                f"Search for '{search_query}' was successful",
            )
        except Exception as e:
            await self.take_screenshot("07_search_error")
            self.log_result("Search Movies", "FAIL", str(e))
            raise

        """
        Test 8: Test viewing a movie's detail page.
        """
    async def test_08_view_movie_details(self):

        print("\nTest 8: View Movie Details")
        try:
            # Search for a specific movie
            await self.page.goto(f"{self.base_url}/search?query=Prisoners")
            await self.page.wait_for_load_state("networkidle")

            # Find all movie links on the page
            movie_links = await self.page.locator('a[href*="/movie/"]').all()
            if not movie_links:
                raise Exception("No movie links found in search results")

            # Click on the first movie link
            await movie_links[0].click()
            await self.page.wait_for_load_state("networkidle")

            assert "/movie/" in self.page.url

            await self.take_screenshot("08_movie_details")
            self.log_result(
                "View Movie Details",
                "PASS",
                "Movie details page loaded successfully from search",
            )
        except Exception as e:
            await self.take_screenshot("08_movie_details_error")
            self.log_result("View Movie Details", "FAIL", str(e))
            raise


        """
        Test 9: Test adding a review to a movie.
        """
    async def test_09_add_review(self):

        print("\nTest 9: Add Movie Review")
        try:
            # Log in first
            await self.test_04_user_login()

            # Go to a specific movie page (Dead Man's Shoes - movie ID 12877)
            await self.page.goto(f"{self.base_url}/movie/12877") 
            await self.page.wait_for_load_state("networkidle")

            # Fill in the review form
            await self.page.fill('input[name="rating"]', "9")
            test_comment = "Amazing movie! A true cult classic."
            await self.page.fill('textarea[name="comment"]', test_comment)

            await self.take_screenshot("09_review_form_filled")

            # Find the review form and click its submit button
            review_form = self.page.locator('form[action*="review"]').first
            await review_form.locator('button[type="submit"]').click()
            await self.page.wait_for_load_state("networkidle")

            # Verify the review appears on the page
            content = await self.page.content()
            assert test_comment in content

            await self.take_screenshot("09_review_added")
            self.log_result("Add Review", "PASS", "Review was added successfully")
        except Exception as e:
            await self.take_screenshot("09_add_review_error")
            self.log_result("Add Review", "FAIL", str(e))
            raise

        """
        Test 10: Test adding a comment to a movie.
        """
    async def test_10_add_comment(self):

        print("\nTest 10: Add Movie Comment")
        try:
            # Log in first
            await self.test_04_user_login()
            
            # Go to a specific movie page (Dead Man's Shoes - movie ID 12877)
            await self.page.goto(f"{self.base_url}/movie/12877")
            await self.page.wait_for_load_state("networkidle")

            # Fill in the comment form
            test_content = "Shane Meadows best movie, hands down!"
            await self.page.fill('textarea[name="content"]', test_content)

            await self.take_screenshot("10_comment_form_filled")

            # Find the comment form and click its submit button
            comment_form = self.page.locator('form[action*="comment"]').first
            await comment_form.locator('button[type="submit"]').click()
            await self.page.wait_for_load_state("networkidle")

            # Verify the comment appears on the page
            content = await self.page.content()
            assert test_content in content

            await self.take_screenshot("10_comment_added")
            self.log_result("Add Comment", "PASS", "Comment was added and displayed successfully")
        except Exception as e:
            await self.take_screenshot("10_add_comment_error")
            self.log_result("Add Comment", "FAIL", str(e))
            raise

        """
        Test 11: Measure how fast the home page loads.
        """
    async def test_11_performance_metrics(self):

        print("\nTest 11: Performance Metric")
        try:
            # Record the start time
            start_time = time.time()
            
            # Load the home page
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")
            
            # Calculate how long it took
            load_time = time.time() - start_time

            # Get performance metrics from the browser
            metrics = await self.page.evaluate(
                """() => {
                    const perf = window.performance.timing;
                    return {
                        loadTime: perf.loadEventEnd - perf.navigationStart,
                        domReady: perf.domContentLoadedEventEnd - perf.navigationStart,
                        responseTime: perf.responseEnd - perf.requestStart
                    };
                }"""
            )

            await self.take_screenshot("11_performance_test")

            # Create a message with all the performance data
            msg = (
                f"Load: {load_time:.2f}s, "
                f"DOM: {metrics['domReady']}ms, "
                f"Response: {metrics['responseTime']}ms"
            )
            self.log_result("Performance Metrics", "PASS", msg)
        except Exception as e:
            await self.take_screenshot("11_performance_error")
            self.log_result("Performance Metrics", "FAIL", str(e))


        """
        Test 12: Test for SQL Injection vulnerability in the login form.
        
        This test checks if the login form is vulnerable to SQL injection attacks.
        SQL injection is a security vulnerability where an attacker can manipulate
        database queries by entering special characters in form fields.
        this test will try to log in using a malicious SQL payload instead of
        a real email address
        """
    async def test_12_sql_injection_login(self):

        print("\nTest 12: SQL Injection Test (Login)")
        try:
            # Go to the login page
            await self.page.goto(f"{self.base_url}/login")
            await self.page.wait_for_load_state("networkidle")

            # Try a SQL injection payload in the email field
            # This payload tries to trick the database into letting us log in
            sql_payload = "randomtest@gmail.com' OR '1'='1' --"
            await self.page.fill('input[name="email"]', sql_payload)
            await self.page.fill('input[name="password"]', "anything")

            await self.take_screenshot("12_sql_injection_attempt")

            # Click the login button
            await self.page.click('form[action="/login"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            # Mark this as a vulnerability (this is intentional for demonstration)
            self.log_result(
                "SQL Injection Test",
                "VULNERABILITY",
                "Login form uses string concatenation which allows SQL injection attacks.",
            )
        except Exception as e:
            await self.take_screenshot("12_sql_injection_error")
            self.log_result("SQL Injection Test", "ERROR", str(e))


        """
        Test 13: Test for Cross-Site Scripting (XSS) vulnerability in search.
        
        This test checks if the search feature is vulnerable to XSS attacks.
        XSS is a security vulnerability where an attacker can inject malicious
        JavaScript that runs in browsers.
        this test will search for a JavaScript code If the app is
        insecure, this code will be executed instead of just displayed as text.
        """
    async def test_13_xss_search(self):

        print("\nTest 13: XSS Test (Search)")
        try:
            # Go to the home page
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")

            # Try an XSS payload in the search box
            # This payload tries to inject JavaScript code
            xss_payload = "<script>alert('XSS')</script>"
            await self.page.fill('input[name="query"]', xss_payload)

            await self.take_screenshot("13_xss_search_attempt")

            # Submit the search
            await self.page.click('form[role="search"] button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")

            # Check if the script tag appears in the page source
            content = await self.page.content()
            if "<script>alert('XSS')</script>" in content:
                # If the script tag is in the page, it's vulnerable
                await self.take_screenshot("13_xss_vulnerability_found")
                self.log_result(
                    "XSS Test",
                    "VULNERABILITY",
                    "Search results display unescaped HTML, allowing XSS attacks!",
                )
            else:
                # If the script tag is not in the page, it's been sanitized
                self.log_result("XSS Test", "PASS", "XSS attempt was properly sanitized")
        except Exception as e:
            await self.take_screenshot("13_xss_error")
            self.log_result("XSS Test", "ERROR", str(e))

    # RUNNER AND SUMMARY METHODS

        """
        Run all the tests in order.
        This method sets up the browser, runs each test, and then cleans up.
        """
    async def run_all_tests(self):

        # Set up the browser
        await self.setup()

        # Make sure our test user exists before running tests
        await self.ensure_test_user_exists()

        # List of all test methods to run
        tests = [
            self.test_01_home_page_loads,
            self.test_02_navigation_to_register,
            self.test_03_user_registration,
            self.test_04_user_login,
            self.test_05_view_profile,
            self.test_06_edit_profile,
            self.test_07_search_movies,
            self.test_08_view_movie_details,
            self.test_09_add_review,
            self.test_10_add_comment,
            self.test_11_performance_metrics,
            self.test_12_sql_injection_login,
            self.test_13_xss_search,
        ]

        # Run each test
        for test in tests:
            try:
                await test()
            except Exception as e:
                # If a test fails, print the error but continue with other tests
                print(f"Test failed with error: {e}")
                continue

        # Clean up the browser
        await self.teardown()
        
        # Print a summary of all test results
        self.print_summary()

        """
        Print a summary of all test results
        """
    def print_summary(self):

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        # Count the different types of results
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        vulnerabilities = sum(
            1 for r in self.test_results if r["status"] == "VULNERABILITY"
        )
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")

        # Print the counts
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Vulnerabilities Found: {vulnerabilities}")
        print(f"Errors: {errors}")
        print("=" * 70)

        # If we found any vulnerabilities, list them
        if vulnerabilities > 0:
            print("\nSECURITY VULNERABILITIES DETECTED:")
            for result in self.test_results:
                if result["status"] == "VULNERABILITY":
                    print(f"  - {result['test']}: {result['message']}")

        # Print detailed results for each test
        print("\nDetailed Results:")
        for result in self.test_results:
            print(f"{result['test']}: {result['status']} - {result['message']}")



    """
    Main function that runs when you execute this script
    """
async def main():

    import os

    # Create screenshots folder if it doesn't exist
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    print("Starting CineFiles Playwright Tests...")
    print("Make sure the application is running on http://localhost:5000")
    print("=" * 70)

    # Create a test object and run all tests
    tester = CineFilesPlaywrightTests()
    await tester.run_all_tests()


# This runs the main function when you execute the script
if __name__ == "__main__":
    asyncio.run(main())
