import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EnterpriseSSOLoginCard } from '../EnterpriseSSOLoginCard';
import { vi, describe, it, expect } from 'vitest';

describe('EnterpriseSSOLoginCard', () => {
  it('renders correctly', () => {
    render(<EnterpriseSSOLoginCard />);

    expect(screen.getByText('Enterprise Login')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('company.com')).toBeInTheDocument();
    expect(screen.getByText('Continue with SSO')).toBeInTheDocument();
    expect(screen.getByText('Google')).toBeInTheDocument();
    expect(screen.getByText('Azure AD')).toBeInTheDocument();
  });

  it('shows error message when domain is empty and submitted', async () => {
    render(<EnterpriseSSOLoginCard />);

    const submitButton = screen.getByText('Continue with SSO');
    fireEvent.click(submitButton);

    expect(await screen.findByText('Please enter your organization domain')).toBeInTheDocument();
  });

  it('shows error message for invalid domain', async () => {
    render(<EnterpriseSSOLoginCard />);

    const input = screen.getByPlaceholderText('company.com');
    const submitButton = screen.getByText('Continue with SSO');

    fireEvent.change(input, { target: { value: 'invalid-domain' } });
    fireEvent.click(submitButton);

    expect(await screen.findByText('Please enter a valid domain (e.g., company.com)')).toBeInTheDocument();
  });

  it('calls onSSOSubmit with valid domain', async () => {
    const mockSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EnterpriseSSOLoginCard onSSOSubmit={mockSubmit} />);

    const input = screen.getByPlaceholderText('company.com');
    const submitButton = screen.getByText('Continue with SSO');

    fireEvent.change(input, { target: { value: 'bijmantra.org' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith('bijmantra.org');
    });
  });

  it('shows loading state during submission', async () => {
    const mockSubmit = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<EnterpriseSSOLoginCard onSSOSubmit={mockSubmit} />);

    const input = screen.getByPlaceholderText('company.com');
    const submitButton = screen.getByText('Continue with SSO');

    fireEvent.change(input, { target: { value: 'bijmantra.org' } });
    fireEvent.click(submitButton);

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText('Continue with SSO')).toBeInTheDocument();
    });
  });

  it('handles Google login click', async () => {
    const consoleSpy = vi.spyOn(console, 'log');
    render(<EnterpriseSSOLoginCard />);

    const googleButton = screen.getByText('Google');
    fireEvent.click(googleButton);

    expect(consoleSpy).toHaveBeenCalledWith('Logging in with Google');
  });

  it('handles Azure AD login click', async () => {
    const consoleSpy = vi.spyOn(console, 'log');
    render(<EnterpriseSSOLoginCard />);

    const azureButton = screen.getByText('Azure AD');
    fireEvent.click(azureButton);

    expect(consoleSpy).toHaveBeenCalledWith('Logging in with Microsoft');
  });
});
