from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.urls import reverse
from tracker.models import Expense, ExpenseRecurringChangeLog, Income, IncomeRecurringChangeLog, ExpenseCategory, IncomeCategory, CreditCard
from datetime import datetime

class AuthViewsTest(APITestCase):

    def setUp(self):
        """Set up a test user and token for authentication"""
        self.user = User.objects.create_user(username='testuser', password='password')
        self.token = Token.objects.create(user=self.user)
    
    def authenticate(self):
        """Helper to authenticate requests with the token"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def unauthenticate(self):
        """Helper to remove authentication from requests"""
        self.client.credentials()

    def test_login_success(self):
        """Test logging in with valid credentials"""
        data = {'username': 'testuser', 'password': 'password'}
        self.unauthenticate()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        """Test logging in with invalid credentials"""
        data = {'username': 'wronguser', 'password': 'wrongpassword'}
        self.unauthenticate()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid Credentials')

    def test_login_already_authenticated(self):
        """Test logging in when already authenticated"""
        data = {'username': 'testuser', 'password': 'password'}
        self.authenticate()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'You are already logged in')

    def test_login_missing_fields(self):
        """Test logging in with missing fields"""
        data = {'username': 'testuser'}
        self.unauthenticate()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_signup_success(self):
        """Test signing up with valid data"""
        data = {'username': 'newuser', 'password': 'newpassword'}
        self.unauthenticate()
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_signup_duplicate_username(self):
        """Test signing up with an existing username"""
        data = {'username': 'testuser', 'password': 'password'}
        self.unauthenticate()
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['username'], 'This username is already in use.')

    def test_signup_already_authenticated(self):
        """Test signing up when already authenticated"""
        data = {'username': 'anotheruser', 'password': 'anotherpassword'}
        self.authenticate()
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'You are already authenticated')

    def test_signup_missing_fields(self):
        """Test signing up with missing fields"""
        data = {'username': 'newuser'}
        self.unauthenticate()
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_logout_success(self):
        """Test logging out with valid token"""
        self.authenticate()
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_without_authentication(self):
        """Test logging out without being authenticated"""
        self.unauthenticate()
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Authentication credentials were not provided.')

    def test_login_inactive_user(self):
        """Test logging in with an inactive user"""
        self.user.is_active = False
        self.user.save()
        data = {'username': 'testuser', 'password': 'password'}
        self.client.credentials()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid Credentials')
class UpdateRecurringExpenseTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        self.expense = Expense.objects.create(user=self.user, amount=100, description='Test Expense')
        self.url = reverse('update_recurring_expense', kwargs={'expense_id': self.expense.id})

    def test_successful_update_existing_log(self):
        """Test updating an existing recurring expense log with all fields"""
        log = ExpenseRecurringChangeLog.objects.create(expense=self.expense, new_amount=150, effective_date='2024-09-20')

        data = {'new_amount': 200, 'effective_date': '2024-09-20'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_amount'], '200.00')

    def test_create_new_log(self):
        """Test creating a new recurring expense log"""
        data = {'new_amount': 200, 'effective_date': '2024-10-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['new_amount'], '200.00')
        self.assertEqual(ExpenseRecurringChangeLog.objects.filter(expense=self.expense).count(), 1)

    def test_missing_effective_date(self):
        """Test that the effective_date field is required"""
        data = {'new_amount': 200}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Effective date is required.')

    def test_invalid_effective_date_format(self):
        """Test validation of effective_date format"""
        data = {'new_amount': 200, 'effective_date': '01/10/2024'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid date format. Use YYYY-MM-DD.')

    def test_invalid_expense_id(self):
        """Test using an invalid or non-existent expense ID (404)"""
        url = reverse('update_recurring_expense', kwargs={'expense_id': 9999})
        data = {'new_amount': 200, 'effective_date': '2024-10-01'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_without_authentication(self):
        """Test that updating without being authenticated returns a 403 error"""
        self.client.logout()
        data = {'new_amount': 200, 'effective_date': '2024-10-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update(self):
        """Test that partial updates (i.e., missing fields) are not allowed"""
        log = ExpenseRecurringChangeLog.objects.create(expense=self.expense, new_amount=150, effective_date='2024-09-20')
        data = {'new_amount': 250}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Effective date is required.')

    def test_create_log_existing_effective_date(self):
        """Test creating a log with an effective_date that already exists"""
        ExpenseRecurringChangeLog.objects.create(expense=self.expense, new_amount=150, effective_date='2024-09-20')
        data = {'new_amount': 200, 'effective_date': '2024-09-20'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_amount'], '200.00')

    def test_create_log_future_effective_date(self):
        """Test creating a log with a future effective date"""
        data = {'new_amount': 300, 'effective_date': '2025-01-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['new_amount'], '300.00')
class UpdateRecurringIncomeTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        self.income = Income.objects.create(user=self.user, amount=1000, description='Test Income')
        self.url = reverse('update_recurring_income', kwargs={'income_id': self.income.id})

    def test_successful_update_existing_log(self):
        """Test updating an existing recurring income log successfully"""
        log = IncomeRecurringChangeLog.objects.create(income=self.income, new_amount=1200, effective_date='2024-09-20')

        data = {'new_amount': 1500, 'effective_date': '2024-09-20'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_amount'], '1500.00')

    def test_create_new_log(self):
        """Test creating a new recurring income log"""
        data = {'new_amount': 2000, 'effective_date': '2024-10-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['new_amount'], '2000.00')
        self.assertEqual(IncomeRecurringChangeLog.objects.filter(income=self.income).count(), 1)

    def test_missing_effective_date(self):
        """Test that the effective_date field is required"""
        data = {'new_amount': 1500}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Effective date is required.')

    def test_invalid_effective_date_format(self):
        """Test validation of effective_date format"""
        data = {'new_amount': 1500, 'effective_date': '01/10/2024'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid date format. Use YYYY-MM-DD.')

    def test_invalid_income_id(self):
        """Test using an invalid or non-existent income ID (404)"""
        url = reverse('update_recurring_income', kwargs={'income_id': 9999})
        data = {'new_amount': 2000, 'effective_date': '2024-10-01'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_without_authentication(self):
        """Test that updating without being authenticated returns a 403 error"""
        self.client.logout()
        data = {'new_amount': 1500, 'effective_date': '2024-10-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update(self):
        """Test that partial updates (i.e., missing fields) are not allowed"""
        log = IncomeRecurringChangeLog.objects.create(income=self.income, new_amount=1200, effective_date='2024-09-20')
        data = {'new_amount': 1800}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Effective date is required.')

    def test_create_log_existing_effective_date(self):
        """Test creating a log with an effective_date that already exists"""
        IncomeRecurringChangeLog.objects.create(income=self.income, new_amount=1200, effective_date='2024-09-20')
        data = {'new_amount': 1500, 'effective_date': '2024-09-20'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_amount'], '1500.00')

    def test_create_log_future_effective_date(self):
        """Test creating a log with a future effective date"""
        data = {'new_amount': 2500, 'effective_date': '2025-01-01'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['new_amount'], '2500.00')
class ExpenseViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='otheruser', password='password')
        self.client.force_authenticate(user=self.user)

    # 1. Successful retrieval of monthly expenses
    def test_retrieve_expenses_for_month(self):
        # Create two regular expenses
        Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 9, 15), is_recurring=False)
        Expense.objects.create(user=self.user, amount=200, date=datetime(2024, 9, 5), is_recurring=True)

        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        self.assertEqual(len(response.data), 2)

    # 2. No expenses for the given month
    def test_no_expenses_for_given_month(self):
        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 3. Filtering expenses for a specific user
    def test_filter_expenses_by_user(self):
        Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 9, 15), is_recurring=False)
        Expense.objects.create(user=self.other_user, amount=200, date=datetime(2024, 9, 5), is_recurring=True)

        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # 4. Recurring expenses with changes in the change_logs
    def test_recurring_expense_with_change_log(self):
        recurring_expense = Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 8, 1), is_recurring=True)
        ExpenseRecurringChangeLog.objects.create(expense=recurring_expense, new_amount=150, effective_date=datetime(2024, 9, 1))

        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], "150.00")

    # 5. Recurring expenses without changes in change_logs
    def test_recurring_expense_without_change_log(self):
        recurring_expense = Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 8, 1), is_recurring=True)

        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], "100.00")

    # 6. Invalid year and month in query parameters
    def test_invalid_year_and_month(self):
        url = reverse('expense-list')
        
        response = self.client.get(url, {'year': 'invalid', 'month': 'invalid'})
    
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.assertIn('Invalid year or month format', str(response.data))

    # 7. Perform create with valid data
    def test_create_expense_valid_data(self):
        url = reverse('expense-list')
        category = ExpenseCategory.objects.create(name='Food')

        data = {
            'amount': 100,
            'date': '2024-09-15',
            'description': 'Test expense',
            'category': category.id,
            'is_recurring': False,
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    # 8. Perform create with recurring expense and valid data
    def test_create_recurring_expense_valid(self):
        url = reverse('expense-list')

        category = ExpenseCategory.objects.create(name='Utilities')

        data = {
            'amount': 200,
            'date': '2024-09-05',
            'description': 'Recurring expense',
            'category': category.id,
            'is_recurring': True,
            'installments': 1
        }
        response = self.client.post(url, data, format='json')

        print("Response status:", response.status_code)
        print("Response data:", response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # 9. Recurring expense with more than 1 installment (invalid)
    def test_create_recurring_expense_invalid_installments(self):
        url = reverse('expense-list')

        category = ExpenseCategory.objects.create(name='Utilities')

        data = {
            'amount': 200,
            'date': '2024-09-05',
            'description': 'Invalid recurring expense',
            'category': category.id,
            'is_recurring': True,
            'installments': 3
        }
        
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('Recurring expenses cannot have more than 1 installment', str(response.data))

    # 10. Non-recurring expense with more than 1 installment (valid)
    def test_create_non_recurring_expense_valid_installments(self):
        url = reverse('expense-list')

        category = ExpenseCategory.objects.create(name='Shopping')

        data = {
            'amount': 300,
            'date': '2024-09-10',
            'description': 'Non-recurring with installments',
            'category': category.id,
            'is_recurring': False,
            'installments': 3 
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # 11. Handle empty query parameters
    def test_empty_query_parameters(self):
        url = reverse('expense-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 12. Handle missing effective date in change_logs
    def test_recurring_expense_missing_effective_date(self):
        recurring_expense = Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 8, 1), is_recurring=True)
        ExpenseRecurringChangeLog.objects.create(expense=recurring_expense, new_amount=150)

        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], "100.00")

    # 13. Expenses that overlap between months
    def test_expense_overlapping_months(self):
        expense = Expense.objects.create(user=self.user, amount=100, date=datetime(2024, 8, 25), is_recurring=False)
        url = reverse('expense-list')
        response = self.client.get(url, {'year': 2024, 'month': 8})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['date'], '2024-08-25')
class IncomeViewSetTestCase(APITestCase):

    def setUp(self):
        """Set up a test user, income categories, and token for authentication"""
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        # Create an income category
        self.category = IncomeCategory.objects.create(name='Salary')

    # Test Case 1: Successful retrieval of monthly incomes
    # This test case checks if the API correctly returns all incomes (both regular and recurring) for a specific month.
    def test_retrieve_incomes_for_month(self):
        # Create two incomes: one recurring, one non-recurring
        Income.objects.create(user=self.user, amount=3000, date=datetime(2024, 9, 15), is_recurring=False, category=self.category)
        Income.objects.create(user=self.user, amount=2000, date=datetime(2024, 9, 1), is_recurring=True, category=self.category)

        url = reverse('income-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        # Check response status and the number of incomes returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # Test Case 2: No incomes for the given month
    # This test checks if the API returns an empty list when no incomes are present for the specified month.
    def test_no_incomes_for_given_month(self):
        url = reverse('income-list')
        response = self.client.get(url, {'year': 2024, 'month': 10})
        
        # Ensure the response is successful and no incomes are returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # Test Case 3: Invalid year or month format
    # This test checks if the API raises a validation error for invalid year or month format.
    def test_invalid_year_and_month(self):
        url = reverse('income-list')
        response = self.client.get(url, {'year': 'invalid', 'month': 'invalid'})
        
        # Ensure validation error is raised
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid year or month format.', str(response.data))

    # Test Case 4: Create non-recurring income
    # This test case checks the creation of a non-recurring income with valid data.
    def test_create_non_recurring_income(self):
        url = reverse('income-list')
        data = {
            'amount': 3000,
            'date': '2024-09-10',
            'description': 'September Salary',
            'category': self.category.id,
            'is_recurring': False
        }
        response = self.client.post(url, data, format='json')

        # Ensure the income is created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '3000.00')

    # Test Case 5: Create recurring income
    # This test case checks the creation of a recurring income.
    def test_create_recurring_income(self):
        url = reverse('income-list')
        data = {
            'amount': 2000,
            'date': '2024-09-01',
            'description': 'Monthly Freelance Income',
            'category': self.category.id,
            'is_recurring': True
        }
        response = self.client.post(url, data, format='json')

        # Ensure the recurring income is created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '2000.00')
        self.assertTrue(response.data['is_recurring'])

    # Test Case 6: Create income with missing fields
    # This test checks the validation error when required fields are missing during income creation.
    def test_create_income_missing_fields(self):
        url = reverse('income-list')
        data = {
            'amount': 3000,  # Missing date and category
        }
        response = self.client.post(url, data, format='json')

        # Ensure validation error is raised
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This field is required.', str(response.data))

    # Test Case 7: Successful update of an income
    # This test checks the update of an existing income with valid data.
    def test_update_income(self):
        income = Income.objects.create(user=self.user, amount=3000, date='2024-09-10', category=self.category)
        url = reverse('income-detail', kwargs={'pk': income.id})
        data = {
            'amount': 3500,
            'date': '2024-09-10',
            'description': 'Updated September Salary',
            'category': self.category.id
        }
        response = self.client.put(url, data, format='json')

        # Ensure the income is updated successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '3500.00')

    # Test Case 8: Delete income
    # This test checks the deletion of an existing income.
    def test_delete_income(self):
        income = Income.objects.create(user=self.user, amount=3000, date='2024-09-10', category=self.category)
        url = reverse('income-detail', kwargs={'pk': income.id})
        
        response = self.client.delete(url)

        # Ensure the income is deleted successfully
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Test Case 9: Create recurring income with effective date in change logs
    # This test case checks if recurring income is correctly handled with effective dates from change logs.
    def test_create_recurring_income_with_change_log(self):
        income = Income.objects.create(user=self.user, amount=2000, date='2024-09-01', is_recurring=True, category=self.category)
        IncomeRecurringChangeLog.objects.create(income=income, new_amount=2500, effective_date='2024-09-01')

        url = reverse('income-list')
        response = self.client.get(url, {'year': 2024, 'month': 9})

        # Debug the response data to see what's being returned
        print("Response data:", response.data)

        # Ensure the income amount reflects the change log
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['amount'], '2500.00')
class CreditCardViewSetTestCase(APITestCase):

    def setUp(self):
        """Set up a test user and two credit cards for that user"""
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        # Create two credit cards for the user
        self.credit_card1 = CreditCard.objects.create(
            user=self.user,
            last_four_digits='1234',
            brand='Visa',
            expire_date=datetime(2025, 12, 31),
            credit_limit=5000.00,
            payment_day=15,
            close_card_day=25
        )
        self.credit_card2 = CreditCard.objects.create(
            user=self.user,
            last_four_digits='5678',
            brand='Mastercard',
            expire_date=datetime(2024, 6, 30),
            credit_limit=3000.00,
            payment_day=10,
            close_card_day=20
        )

    # Test Case 1: Retrieve all credit cards for the authenticated user
    def test_retrieve_credit_cards(self):
        """Test retrieving credit cards for the authenticated user"""
        url = reverse('creditcard-list')
        response = self.client.get(url)

        # Check response status and number of credit cards returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # Test Case 2: Create a new credit card with valid data
    def test_create_credit_card(self):
        """Test creating a new credit card"""
        url = reverse('creditcard-list')
        data = {
            'last_four_digits': '9876',
            'brand': 'Amex',
            'expire_date': '2026-05-31',
            'credit_limit': 7000.00,
            'payment_day': 28,  # Ensure payment day is after close card day
            'close_card_day': 25
        }
        response = self.client.post(url, data, format='json')

        # Debug the response data
        print("Response data (Create):", response.data)

        # Ensure the credit card is created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # Test Case 3: Create a new credit card with missing fields
    def test_create_credit_card_missing_fields(self):
        """Test validation when creating a credit card with missing fields"""
        url = reverse('creditcard-list')
        data = {
            'last_four_digits': '3456',
            # Missing 'brand' and 'expire_date'
            'credit_limit': 5000.00,
            'payment_day': 15,
            'close_card_day': 25
        }
        response = self.client.post(url, data, format='json')

        # Ensure validation error is raised
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('brand', response.data)
        self.assertIn('expire_date', response.data)

    # Test Case 4: Update an existing credit card
    def test_update_credit_card(self):
        """Test updating an existing credit card"""
        url = reverse('creditcard-detail', kwargs={'pk': self.credit_card1.id})
        data = {
            'last_four_digits': '1234',
            'brand': 'Visa Platinum',
            'expire_date': '2025-12-31',
            'credit_limit': 6000.00,
            'payment_day': 30,  # Ensure payment day is after close card day
            'close_card_day': 28
        }
        response = self.client.put(url, data, format='json')

        # Debug the response data
        print("Response data (Update):", response.data)

        # Ensure the credit card is updated successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Test Case 5: Delete a credit card
    def test_delete_credit_card(self):
        """Test deleting an existing credit card"""
        url = reverse('creditcard-detail', kwargs={'pk': self.credit_card1.id})
        response = self.client.delete(url)

        # Ensure the credit card is deleted successfully
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Test Case 6: Unauthorized access to credit cards
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access credit cards"""
        self.client.logout()
        url = reverse('creditcard-list')
        response = self.client.get(url)

        # Adjust expectation to 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    # Test Case 7: Access credit cards belonging to another user (should return empty list)
    def test_access_other_user_credit_cards(self):
        """Test that users cannot access credit cards belonging to others"""
        # Create a new user and a credit card for that user
        other_user = User.objects.create_user(username='otheruser', password='password')
        CreditCard.objects.create(
            user=other_user,
            last_four_digits='4321',
            brand='Discover',
            expire_date=datetime(2025, 8, 31),
            credit_limit=4000.00,
            payment_day=20,
            close_card_day=10
        )

        url = reverse('creditcard-list')
        response = self.client.get(url)

        # Ensure the other user's credit card is not returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only the current user's cards