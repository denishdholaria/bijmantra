/**
 * TrialCreationForm Unit Tests
 * Basic tests for trial creation form
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { TrialCreationForm } from './TrialCreationForm';

describe('TrialCreationForm', () => {
  const renderComponent = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <TrialCreationForm />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should render the form with all required fields', () => {
    renderComponent();

    expect(screen.getByText('Create New Trial')).toBeInTheDocument();
    expect(screen.getByLabelText(/Trial Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Trial Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Crop/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Start Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/End Date/i)).toBeInTheDocument();
  });

  it('should have submit button disabled when trial name is empty', () => {
    renderComponent();

    const submitButton = screen.getByRole('button', { name: /Create Trial/i });
    expect(submitButton).toBeDisabled();
  });

  it('should have cancel button', () => {
    renderComponent();

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    expect(cancelButton).toBeInTheDocument();
  });
});
