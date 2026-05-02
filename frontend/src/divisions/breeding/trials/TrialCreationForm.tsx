/**
 * Trial Creation Form
 * Complete bounded workflow for creating breeding trials
 * Implements all 4 states: loading, empty, error, success
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrialCreation } from './useTrialCreation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import type { TrialFormData } from './types';

export function TrialCreationForm() {
  const navigate = useNavigate();
  const { isLoading, isEmpty, error, success, createdTrialId, createTrial, resetState } = useTrialCreation();

  const [formData, setFormData] = useState<TrialFormData>({
    trialName: '',
    trialDescription: '',
    trialType: '',
    startDate: '',
    endDate: '',
    active: true,
    commonCropName: '',
  });

  const handleInputChange = (field: keyof TrialFormData, value: string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.trialName.trim()) {
      return;
    }

    createTrial(formData);
  };

  const handleReset = () => {
    setFormData({
      trialName: '',
      trialDescription: '',
      trialType: '',
      startDate: '',
      endDate: '',
      active: true,
      commonCropName: '',
    });
    resetState();
  };

  const handleViewTrial = () => {
    if (createdTrialId) {
      navigate(`/trials/${createdTrialId}`);
    }
  };

  // Loading State
  if (isLoading) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600" />
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              Creating trial...
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Please wait while we set up your breeding trial
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Success State
  if (success && createdTrialId) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="rounded-full bg-green-100 dark:bg-green-900 p-3">
              <CheckCircle2 className="h-12 w-12 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Trial Created Successfully!
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-center max-w-md">
              Your breeding trial "{formData.trialName}" has been created and is ready for use.
            </p>
            <div className="flex gap-3 pt-4">
              <Button onClick={handleViewTrial} size="lg">
                View Trial
              </Button>
              <Button onClick={handleReset} variant="outline" size="lg">
                Create Another Trial
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error State
  if (error) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Error creating trial:</strong> {error}
            </AlertDescription>
          </Alert>
          <div className="flex justify-center gap-3">
            <Button onClick={() => resetState()} variant="outline">
              Try Again
            </Button>
            <Button onClick={() => navigate('/trials')} variant="ghost">
              Back to Trials
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty State (Form)
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Trial</CardTitle>
        <CardDescription>
          Set up a new breeding trial to organize your studies and experiments
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Trial Name - Required */}
          <div className="space-y-2">
            <Label htmlFor="trialName">
              Trial Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="trialName"
              value={formData.trialName}
              onChange={(e) => handleInputChange('trialName', e.target.value)}
              placeholder="e.g., 2024 Wheat Yield Trial"
              required
            />
          </div>

          {/* Trial Description */}
          <div className="space-y-2">
            <Label htmlFor="trialDescription">Description</Label>
            <Textarea
              id="trialDescription"
              value={formData.trialDescription}
              onChange={(e) => handleInputChange('trialDescription', e.target.value)}
              placeholder="Describe the purpose and objectives of this trial"
              rows={3}
            />
          </div>

          {/* Trial Type */}
          <div className="space-y-2">
            <Label htmlFor="trialType">Trial Type</Label>
            <Input
              id="trialType"
              value={formData.trialType}
              onChange={(e) => handleInputChange('trialType', e.target.value)}
              placeholder="e.g., Yield Trial, Disease Resistance, Quality Assessment"
            />
          </div>

          {/* Crop Name */}
          <div className="space-y-2">
            <Label htmlFor="commonCropName">Crop</Label>
            <Input
              id="commonCropName"
              value={formData.commonCropName}
              onChange={(e) => handleInputChange('commonCropName', e.target.value)}
              placeholder="e.g., Wheat, Rice, Maize"
            />
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                type="date"
                value={formData.startDate}
                onChange={(e) => handleInputChange('startDate', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                type="date"
                value={formData.endDate}
                onChange={(e) => handleInputChange('endDate', e.target.value)}
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/trials')}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!formData.trialName.trim()}
            >
              Create Trial
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
