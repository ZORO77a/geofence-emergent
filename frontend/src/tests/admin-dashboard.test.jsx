import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AdminDashboard from '../pages/AdminDashboard';
import axios from 'axios';

jest.mock('axios');

const mockEmployees = [];
const mockLogs = [
  { employee_username: 'alice', success: true, action: 'download', timestamp: new Date().toISOString(), filename: 'file1' },
  { employee_username: 'bob', success: false, action: 'download', timestamp: new Date().toISOString(), filename: 'file2' }
];
const mockWfh = [];
const mockFiles = [];
const mockConfig = { latitude: 0, longitude: 0, radius: 100, allowed_ssid: '', start_time: '09:00', end_time: '17:00' };

describe('AdminDashboard suspicious flow', () => {
  beforeEach(() => {
    axios.get.mockImplementation((url) => {
      if (url.endsWith('/admin/employees')) return Promise.resolve({ data: mockEmployees });
      if (url.endsWith('/admin/access-logs')) return Promise.resolve({ data: mockLogs });
      if (url.endsWith('/admin/wfh-requests')) return Promise.resolve({ data: mockWfh });
      if (url.endsWith('/files')) return Promise.resolve({ data: mockFiles });
      if (url.endsWith('/admin/geofence-config')) return Promise.resolve({ data: mockConfig });
      return Promise.resolve({ data: {} });
    });
  });

  test('clicking suspicious activity opens logs filtered', async () => {
    render(<AdminDashboard />);

    // Wait for initial loads
    await waitFor(() => expect(axios.get).toHaveBeenCalled());

    const suspiciousCard = screen.getByText(/Suspicious Activity/i).closest('div');
    fireEvent.click(suspiciousCard);

    // Expect logs table to show only the failing entry
    await waitFor(() => {
      expect(screen.getByText('Access Logs')).toBeInTheDocument();
      expect(screen.queryByText('alice')).not.toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  });
});
