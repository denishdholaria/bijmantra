/**
 * Integrations Dashboard
 *
 * Third-party API connections and external service integrations.
 * Connected to backend: /api/v2/integrations
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AvailableIntegration {
  type: string;
  name: string;
  description: string;
  required_fields: string[];
  optional_fields: string[];
  docs_url: string;
  icon: string;
}

interface UserIntegration {
  id: string;
  user_id: string;
  organization_id: string;
  integration_type: string;
  name: string;
  status: string;
  last_used: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export function Dashboard() {
  const [availableIntegrations, setAvailableIntegrations] = useState<AvailableIntegration[]>([]);
  const [userIntegrations, setUserIntegrations] = useState<UserIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('');
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [integrationName, setIntegrationName] = useState('');
  const { toast } = useToast();

  // Fetch available integrations and user's integrations
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [availableRes, userRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/integrations/available`),
        fetch(`${API_BASE}/api/v2/integrations/`),
      ]);

      if (availableRes.ok) {
        const data = await availableRes.json();
        setAvailableIntegrations(data.integrations || []);
      }

      if (userRes.ok) {
        const data = await userRes.json();
        setUserIntegrations(data || []);
      }
    } catch (error) {
      console.error('Failed to fetch integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectedIntegration = availableIntegrations.find(i => i.type === selectedType);

  const handleAddIntegration = async () => {
    if (!selectedType || !integrationName) {
      toast({ title: 'Error', description: 'Please fill in all required fields', variant: 'destructive' });
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v2/integrations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          integration_type: selectedType,
          name: integrationName,
          credentials: formData,
        }),
      });

      if (res.ok) {
        toast({ title: 'Success', description: 'Integration added successfully' });
        setDialogOpen(false);
        setSelectedType('');
        setFormData({});
        setIntegrationName('');
        fetchData();
      } else {
        const error = await res.json();
        toast({ title: 'Error', description: error.detail || 'Failed to add integration', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to connect to server', variant: 'destructive' });
    }
  };

  const handleTestConnection = async (integrationId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/integrations/${integrationId}/test`, {
        method: 'POST',
      });
      const data = await res.json();

      if (data.success) {
        toast({ title: 'Success', description: data.message || 'Connection successful' });
      } else {
        toast({ title: 'Connection Failed', description: data.error || 'Unknown error', variant: 'destructive' });
      }
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to test connection', variant: 'destructive' });
    }
  };

  const handleDeleteIntegration = async (integrationId: string) => {
    if (!confirm('Are you sure you want to delete this integration?')) return;

    try {
      const res = await fetch(`${API_BASE}/api/v2/integrations/${integrationId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        toast({ title: 'Deleted', description: 'Integration removed' });
        fetchData();
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete integration', variant: 'destructive' });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700';
      case 'error': return 'bg-red-100 text-red-700';
      case 'pending': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Integration Hub</h1>
          <p className="text-gray-600 mt-1">Connect with external systems and services</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>+ Add Integration</Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Integration</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>Integration Type</Label>
                <Select value={selectedType} onValueChange={(v) => { setSelectedType(v); setFormData({}); }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select integration type" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableIntegrations.map((i) => (
                      <SelectItem key={i.type} value={i.type}>
                        {i.icon} {i.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Name</Label>
                <Input
                  placeholder="My NCBI Connection"
                  value={integrationName}
                  onChange={(e) => setIntegrationName(e.target.value)}
                />
              </div>

              {selectedIntegration && (
                <>
                  <p className="text-sm text-gray-600">{selectedIntegration.description}</p>
                  {selectedIntegration.required_fields.map((field) => (
                    <div key={field}>
                      <Label>{field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} *</Label>
                      <Input
                        type={field.includes('key') || field.includes('secret') ? 'password' : 'text'}
                        value={formData[field] || ''}
                        onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                      />
                    </div>
                  ))}
                  {selectedIntegration.optional_fields.map((field) => (
                    <div key={field}>
                      <Label>{field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</Label>
                      <Input
                        value={formData[field] || ''}
                        onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                      />
                    </div>
                  ))}
                  {selectedIntegration.docs_url && (
                    <a href={selectedIntegration.docs_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                      📖 View Documentation
                    </a>
                  )}
                </>
              )}

              <Button onClick={handleAddIntegration} className="w-full">
                Add Integration
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* User's Integrations */}
      {userIntegrations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Your Integrations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {userIntegrations.map((integration) => {
                const config = availableIntegrations.find(a => a.type === integration.integration_type);
                return (
                  <div key={integration.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{config?.icon || '🔗'}</span>
                        <div>
                          <h4 className="font-medium">{integration.name}</h4>
                          <p className="text-sm text-gray-600">{config?.name || integration.integration_type}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(integration.status)}`}>
                          {integration.status}
                        </span>
                        <Button variant="outline" size="sm" onClick={() => handleTestConnection(integration.id)}>
                          Test
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteIntegration(integration.id)}>
                          🗑️
                        </Button>
                      </div>
                    </div>
                    {integration.last_error && (
                      <p className="text-sm text-red-600 mt-2">Error: {integration.last_error}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Integrations */}
      <Card>
        <CardHeader>
          <CardTitle>Available Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {availableIntegrations.map((integration) => (
                <div key={integration.type} className="p-4 border rounded-lg hover:border-green-300 transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{integration.icon}</span>
                    <div>
                      <h4 className="font-medium">{integration.name}</h4>
                      <p className="text-sm text-gray-600">{integration.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
