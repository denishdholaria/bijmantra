/**
 * Create Workspace Wizard
 * 
 * 3-step wizard for creating custom workspaces:
 * 1. Basic Info (name, description, icon, color)
 * 2. Select Pages
 * 3. Review & Create
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ChevronLeft, ChevronRight, Check, Sparkles, File } from 'lucide-react';
import { getWorkspaceIcon, WORKSPACE_ICON_MAP } from '@/lib/workspace-icons';
import { PagePicker } from './PagePicker';
import { useWorkspaceActions, useSelectablePages } from '@/hooks/useCustomWorkspace';
import { workspaceTemplates, getTemplate } from '@/data/workspaceTemplates';
import { 
  WORKSPACE_COLORS, 
  WORKSPACE_ICONS,
  CUSTOM_WORKSPACE_LIMITS,
  type WorkspaceColor,
} from '@/types/customWorkspace';

interface CreateWorkspaceWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated?: (workspaceId: string) => void;
}

type Step = 1 | 2 | 3;

interface FormData {
  name: string;
  description: string;
  icon: string;
  color: WorkspaceColor;
  pageIds: string[];
  templateId?: string;
}

const initialFormData: FormData = {
  name: '',
  description: '',
  icon: 'Sprout',
  color: 'green',
  pageIds: [],
};

export function CreateWorkspaceWizard({ 
  open, 
  onOpenChange,
  onCreated,
}: CreateWorkspaceWizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [error, setError] = useState<string | null>(null);
  
  const { create } = useWorkspaceActions();
  const modules = useSelectablePages();
  
  // Reset form when dialog closes
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setStep(1);
      setFormData(initialFormData);
      setError(null);
    }
    onOpenChange(open);
  };
  
  // Apply template
  const applyTemplate = (templateId: string) => {
    const template = getTemplate(templateId);
    if (template) {
      setFormData({
        name: template.name,
        description: template.description,
        icon: template.icon,
        color: template.color,
        pageIds: template.pageIds,
        templateId: template.id,
      });
    }
  };
  
  // Validate step 1
  const validateStep1 = (): boolean => {
    if (!formData.name.trim()) {
      setError('Name is required');
      return false;
    }
    if (formData.name.length > CUSTOM_WORKSPACE_LIMITS.maxNameLength) {
      setError(`Name must be ${CUSTOM_WORKSPACE_LIMITS.maxNameLength} characters or less`);
      return false;
    }
    if (formData.description && formData.description.length > CUSTOM_WORKSPACE_LIMITS.maxDescriptionLength) {
      setError(`Description must be ${CUSTOM_WORKSPACE_LIMITS.maxDescriptionLength} characters or less`);
      return false;
    }
    setError(null);
    return true;
  };
  
  // Validate step 2
  const validateStep2 = (): boolean => {
    if (formData.pageIds.length < CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace) {
      setError(`Select at least ${CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace} page`);
      return false;
    }
    setError(null);
    return true;
  };
  
  // Handle next step
  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };
  
  // Handle back
  const handleBack = () => {
    setError(null);
    if (step === 2) setStep(1);
    else if (step === 3) setStep(2);
  };
  
  // Handle create
  const handleCreate = () => {
    const workspaceId = create({
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      icon: formData.icon,
      color: formData.color,
      pageIds: formData.pageIds,
      templateId: formData.templateId,
    });
    
    if (workspaceId) {
      onCreated?.(workspaceId);
      handleOpenChange(false);
    } else {
      setError('Failed to create workspace. You may have reached the maximum limit.');
    }
  };
  
  // Get grouped pages for review
  const getGroupedPages = () => {
    const pageIdSet = new Set(formData.pageIds);
    return modules
      .map(module => ({
        ...module,
        pages: module.pages.filter(p => pageIdSet.has(p.id)),
      }))
      .filter(module => module.pages.length > 0);
  };
  
  // Get icon component
  const IconComponent = getWorkspaceIcon(formData.icon, File);
  
  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Create Custom Workspace</DialogTitle>
          <DialogDescription>
            Step {step} of 3: {step === 1 ? 'Basic Info' : step === 2 ? 'Select Pages' : 'Review'}
          </DialogDescription>
        </DialogHeader>
        
        {/* Progress indicator */}
        <div className="flex items-center gap-2 py-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${s < step ? 'bg-primary text-primary-foreground' : 
                  s === step ? 'bg-primary text-primary-foreground' : 
                  'bg-muted text-muted-foreground'}`}
              >
                {s < step ? <Check className="h-4 w-4" /> : s}
              </div>
              {s < 3 && (
                <div className={`flex-1 h-0.5 ${s < step ? 'bg-primary' : 'bg-muted'}`} />
              )}
            </div>
          ))}
        </div>
        
        {/* Error message */}
        {error && (
          <div className="bg-destructive/10 text-destructive text-sm px-4 py-2 rounded-md">
            {error}
          </div>
        )}
        
        {/* Step content */}
        <div className="flex-1 overflow-hidden">
          {step === 1 && (
            <Step1BasicInfo
              formData={formData}
              setFormData={setFormData}
              onApplyTemplate={applyTemplate}
            />
          )}
          
          {step === 2 && (
            <Step2SelectPages
              selectedPageIds={formData.pageIds}
              onSelectionChange={(pageIds) => setFormData(prev => ({ ...prev, pageIds }))}
            />
          )}
          
          {step === 3 && (
            <Step3Review
              formData={formData}
              groupedPages={getGroupedPages()}
              IconComponent={IconComponent}
            />
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div>
            {step === 1 && (
              <Select onValueChange={applyTemplate}>
                <SelectTrigger className="w-[200px]">
                  <Sparkles className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Start from template" />
                </SelectTrigger>
                <SelectContent>
                  {workspaceTemplates.map(template => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            
            {step > 1 && (
              <Button variant="outline" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
            
            {step < 3 ? (
              <Button onClick={handleNext}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button onClick={handleCreate}>
                <Check className="h-4 w-4 mr-1" />
                Create
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Step 1: Basic Info
interface Step1Props {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  onApplyTemplate: (templateId: string) => void;
}

function Step1BasicInfo({ formData, setFormData }: Step1Props) {
  return (
    <div className="space-y-6 py-4">
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="name">Name *</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="My Field Day"
          maxLength={CUSTOM_WORKSPACE_LIMITS.maxNameLength}
        />
        <p className="text-xs text-muted-foreground">
          {formData.name.length}/{CUSTOM_WORKSPACE_LIMITS.maxNameLength} characters
        </p>
      </div>
      
      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description (optional)</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="Pages I use during field visits"
          maxLength={CUSTOM_WORKSPACE_LIMITS.maxDescriptionLength}
          rows={2}
        />
        <p className="text-xs text-muted-foreground">
          {formData.description.length}/{CUSTOM_WORKSPACE_LIMITS.maxDescriptionLength} characters
        </p>
      </div>
      
      {/* Icon */}
      <div className="space-y-2">
        <Label>Icon</Label>
        <div className="flex flex-wrap gap-2">
          {WORKSPACE_ICONS.slice(0, 20).map(iconName => {
            const Icon = WORKSPACE_ICON_MAP[iconName];
            if (!Icon) return null;
            return (
              <button
                key={iconName}
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, icon: iconName }))}
                className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors
                  ${formData.icon === iconName 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted hover:bg-muted/80'}`}
              >
                <Icon className="h-5 w-5" />
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Color */}
      <div className="space-y-2">
        <Label>Color</Label>
        <div className="flex gap-2">
          {(Object.keys(WORKSPACE_COLORS) as WorkspaceColor[]).map(color => (
            <button
              key={color}
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, color }))}
              className={`w-10 h-10 rounded-lg bg-gradient-to-br ${WORKSPACE_COLORS[color].gradient}
                ${formData.color === color ? 'ring-2 ring-offset-2 ring-primary' : ''}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// Step 2: Select Pages
interface Step2Props {
  selectedPageIds: string[];
  onSelectionChange: (pageIds: string[]) => void;
}

function Step2SelectPages({ selectedPageIds, onSelectionChange }: Step2Props) {
  return (
    <div className="py-4">
      <PagePicker
        selectedPageIds={selectedPageIds}
        onSelectionChange={onSelectionChange}
        maxHeight="350px"
      />
    </div>
  );
}

// Step 3: Review
interface Step3Props {
  formData: FormData;
  groupedPages: Array<{ id: string; name: string; pages: Array<{ id: string; name: string }> }>;
  IconComponent: React.ComponentType<{ className?: string }>;
}

function Step3Review({ formData, groupedPages, IconComponent }: Step3Props) {
  const colorConfig = WORKSPACE_COLORS[formData.color];
  
  return (
    <ScrollArea className="h-[350px] pr-4">
      <div className="space-y-6 py-4">
        {/* Preview card */}
        <div className={`rounded-xl p-6 ${colorConfig.bg} ${colorConfig.border} border-2`}>
          <div className="flex items-start gap-4">
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${colorConfig.gradient} flex items-center justify-center shadow-lg`}>
              <IconComponent className="h-7 w-7 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold">{formData.name}</h3>
              {formData.description && (
                <p className="text-muted-foreground mt-1">{formData.description}</p>
              )}
              <div className="flex items-center gap-2 mt-3">
                <Badge variant="secondary">{formData.pageIds.length} pages</Badge>
                <Badge variant="secondary">{groupedPages.length} modules</Badge>
                {formData.templateId && (
                  <Badge variant="outline">From template</Badge>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Selected pages by module */}
        <div className="space-y-4">
          <h4 className="font-medium">Selected Pages</h4>
          {groupedPages.map(module => (
            <div key={module.id} className="space-y-2">
              <h5 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                {module.name}
              </h5>
              <div className="flex flex-wrap gap-2">
                {module.pages.map(page => (
                  <Badge key={page.id} variant="secondary">
                    {page.name}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </ScrollArea>
  );
}

export default CreateWorkspaceWizard;
