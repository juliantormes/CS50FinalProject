import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import ViewExpenses from '../../views/ViewExpenses'; 
import { useAuth } from '../../hooks/useAuth';
import { useFetchFinancialData } from '../../hooks/useFetchFinancialData';
import axiosInstance from '../../api/axiosApi';

// Mock hooks and API instance
jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useFetchFinancialData');
jest.mock('../../api/axiosApi');

beforeAll(() => {
    global.ResizeObserver = class {
        constructor() {}
        observe() {}
        unobserve() {}
        disconnect() {}
    };
});

beforeEach(() => {
  jest.clearAllMocks();
  
  useAuth.mockReturnValue({
    logout: jest.fn(),
  });

  useFetchFinancialData.mockReturnValue({
    data: { expenses: [] },
    refetch: jest.fn(),
  });
});

describe('ViewExpenses Component', () => {
  const categoriesMock = [
    { id: 1, name: 'Utilities' },
    { id: 2, name: 'Groceries' }
  ];
  const creditCardsMock = [
    { id: 1, brand: 'Visa', last_four_digits: '1111' }
  ];

  const renderComponent = () => {
    render(
      <Router>
        <ViewExpenses categories={categoriesMock} creditCards={creditCardsMock} />
      </Router>
    );
  };

  it('renders with expenses data', async () => {
    useFetchFinancialData.mockReturnValueOnce({
      data: {
        expenses: [
          {
            id: 1,
            date: '2024-10-01',
            amount: 100,
            category: 1,
            description: 'Electricity',
            is_recurring: true,
            pay_with_credit_card: true,
            credit_card: { id: 1 },
            installments: 3,
            surcharge: 0,
          },
          {
            id: 2,
            date: '2024-10-15',
            amount: 250,
            category: 2,
            description: 'Groceries',
            is_recurring: false,
            pay_with_credit_card: false,
            credit_card_id: null,
            installments: 0,
            surcharge: 0,
          },
        ],
      },
      refetch: jest.fn(),
    });
    
    renderComponent();

    // Verify that the table rows are rendered for the expenses
    const expenseRow1 = await screen.findByTestId('expense-row-1');
    const expenseRow2 = await screen.findByTestId('expense-row-2');

    expect(expenseRow1).toBeInTheDocument();
    expect(expenseRow2).toBeInTheDocument();

    // Verify specific expense content
    expect(expenseRow1).toHaveTextContent('Utilities'); 
    expect(expenseRow1).toHaveTextContent('Electricity');
    expect(expenseRow1).toHaveTextContent('100');
    expect(expenseRow1).toHaveTextContent('Yes');
    expect(expenseRow1).toHaveTextContent('Visa **** 1111'); 
    expect(expenseRow1).toHaveTextContent('3');  
    expect(expenseRow1).toHaveTextContent('0.00'); 

    expect(expenseRow2).toHaveTextContent('Groceries'); 
    expect(expenseRow2).toHaveTextContent('Groceries');
    expect(expenseRow2).toHaveTextContent('250');
    expect(expenseRow2).toHaveTextContent('No');
    expect(expenseRow2).toHaveTextContent('N/A'); 
    expect(expenseRow2).toHaveTextContent('1');  
    expect(expenseRow2).toHaveTextContent('0.00'); 
  });

  it('handles updating the description of a non-recurring expense', async () => {
    const initialMockData = {
      expenses: [
        {
          id: 1,
          date: '2024-10-01',
          amount: 100,
          category: 1,
          description: 'Electricity', 
          is_recurring: false,
          pay_with_credit_card: false,
          installments: 0,
          surcharge: 0,
        },
      ],
    };

    const mockRefetch = jest.fn(() => {
      useFetchFinancialData.mockReturnValue({
        data: {
          expenses: [
            {
              ...initialMockData.expenses[0],
              description: 'Updated Description', 
            },
          ],
        },
        refetch: mockRefetch,
      });
    });

    useFetchFinancialData.mockReturnValue({
      data: initialMockData,
      refetch: mockRefetch,
    });
  
    renderComponent();

    const editButton = screen.getByRole('button', { name: /edit/i });
    fireEvent.click(editButton);

    const descriptionInput = screen.getByDisplayValue('Electricity');
    fireEvent.change(descriptionInput, { target: { value: 'Updated Description' } });

    const saveIcon = screen.getByTestId('SaveIcon');
    fireEvent.click(saveIcon);

    mockRefetch();

    await waitFor(() => {
      const expenseRow1 = screen.getByTestId('expense-row-1');
      expect(expenseRow1).toHaveTextContent('Updated Description');
    });
  });

  it('handles deleting an expense', async () => {
    useFetchFinancialData.mockReturnValueOnce({
      data: { expenses: [{ id: 1, date: '2024-10-01', amount: 100, category: 'Utilities' }] },
      refetch: jest.fn(),
    });

    axiosInstance.delete.mockResolvedValueOnce({ status: 204 });

    renderComponent();

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.queryByText(/Utilities/i)).not.toBeInTheDocument();
    });
  });

  it('displays error message when saving an expense fails', async () => {
    useFetchFinancialData.mockReturnValueOnce({
      data: { expenses: [{ id: 1, date: '2024-10-01', amount: 100, category: 'Utilities' }] },
      refetch: jest.fn(),
    });

    axiosInstance.put.mockRejectedValueOnce(new Error('Failed to save expense'));

    renderComponent();

    const editButton = screen.getByRole('button', { name: /edit/i });
    fireEvent.click(editButton);

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to save the expense. Please try again./i)).toBeInTheDocument();
    });
  });
});
