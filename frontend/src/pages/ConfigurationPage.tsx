/**
 * Agent Configuration Page
 * 
 * Allows administrators to:
 * - Select scenario type (Dispatch Check-In, Emergency)
 * - Edit system prompts and initial messages
 * - Configure Retell AI settings (Task A requirements)
 * - Load preset templates
 * - Save and activate configurations
 */

import { useState, useEffect } from 'react';
import { 
  Settings, 
  Save, 
  Play, 
  FileText, 
  Sparkles,
  ChevronDown,
  Check,
  AlertCircle,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  Button,
  Input,
  Textarea,
  Toggle,
  Slider,
  Badge,
} from '@/components/ui';
import { 
  useConfigs, 
  useCreateConfig, 
  useUpdateConfig, 
  useActivateConfig 
} from '@/hooks/useConfigs';
import { getTemplatesForScenario } from '@/services/templates';
import type { AgentConfigCreate, ScenarioType, PromptTemplate } from '@/types';

// Scenario options for the dropdown
const SCENARIO_OPTIONS = [
  { value: 'dispatch_checkin', label: 'Dispatch Check-In' },
  { value: 'emergency', label: 'Emergency Protocol' },
];

export function ConfigurationPage() {
  // Form state
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>('dispatch_checkin');
  const [formData, setFormData] = useState<AgentConfigCreate>({
    name: '',
    description: '',
    scenario_type: 'dispatch_checkin',
    system_prompt: '',
    initial_message: '',
    enable_backchanneling: true,
    enable_filler_words: true,
    interruption_sensitivity: 0.5,
    is_active: false,
  });
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // API hooks
  const { data: configs, isLoading: loadingConfigs } = useConfigs();
  const createMutation = useCreateConfig();
  const updateMutation = useUpdateConfig();
  const activateMutation = useActivateConfig();

  // Get configs for current scenario
  const scenarioConfigs = configs?.filter((c) => c.scenario_type === selectedScenario) || [];
  const activeConfig = scenarioConfigs.find((c) => c.is_active);

  // Get templates for current scenario
  const availableTemplates = getTemplatesForScenario(selectedScenario);

  // Load config into form when selected
  useEffect(() => {
    if (selectedConfigId) {
      const config = configs?.find((c) => c.id === selectedConfigId);
      if (config) {
        setFormData({
          name: config.name,
          description: config.description || '',
          scenario_type: config.scenario_type,
          system_prompt: config.system_prompt,
          initial_message: config.initial_message || '',
          enable_backchanneling: config.enable_backchanneling,
          enable_filler_words: config.enable_filler_words,
          interruption_sensitivity: config.interruption_sensitivity,
          is_active: config.is_active,
        });
      }
    }
  }, [selectedConfigId, configs]);

  // Handle scenario change
  const handleScenarioChange = (scenario: ScenarioType) => {
    setSelectedScenario(scenario);
    setSelectedConfigId(null);
    setFormData((prev) => ({
      ...prev,
      scenario_type: scenario,
      name: '',
      description: '',
      system_prompt: '',
      initial_message: '',
    }));
  };

  // Load a template
  const handleLoadTemplate = (template: PromptTemplate) => {
    setFormData((prev) => ({
      ...prev,
      name: template.name,
      description: template.description,
      system_prompt: template.system_prompt,
      initial_message: template.initial_message,
    }));
    setShowTemplates(false);
    setSelectedConfigId(null);
  };

  // Save configuration
  const handleSave = async () => {
    try {
      if (selectedConfigId) {
        await updateMutation.mutateAsync({
          id: selectedConfigId,
          data: formData,
        });
      } else {
        const newConfig = await createMutation.mutateAsync(formData);
        setSelectedConfigId(newConfig.id);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save:', error);
    }
  };

  // Activate configuration
  const handleActivate = async () => {
    if (selectedConfigId) {
      await activateMutation.mutateAsync(selectedConfigId);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const isActivating = activateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Agent Configuration</h1>
        <p className="text-slate-600 mt-1">
          Configure prompts and voice settings for your AI agent
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Configuration Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Scenario Selection */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-slate-600" />
                <h2 className="text-lg font-semibold text-slate-900">Scenario Type</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                {SCENARIO_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleScenarioChange(option.value as ScenarioType)}
                    className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                      selectedScenario === option.value
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="text-left">
                      <div className={`font-medium ${
                        selectedScenario === option.value ? 'text-indigo-900' : 'text-slate-900'
                      }`}>
                        {option.label}
                      </div>
                      <div className="text-sm text-slate-500 mt-1">
                        {option.value === 'dispatch_checkin' 
                          ? 'Driver status updates and ETA collection'
                          : 'Handle emergencies and escalate to humans'
                        }
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Prompt Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-slate-600" />
                  <h2 className="text-lg font-semibold text-slate-900">Prompt Configuration</h2>
                </div>
                <div className="relative">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowTemplates(!showTemplates)}
                    rightIcon={<ChevronDown className="h-4 w-4" />}
                  >
                    <Sparkles className="h-4 w-4" />
                    Load Template
                  </Button>
                  
                  {/* Templates Dropdown */}
                  {showTemplates && (
                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-slate-200 z-10">
                      <div className="p-2">
                        {availableTemplates.map((template) => (
                          <button
                            key={template.id}
                            onClick={() => handleLoadTemplate(template)}
                            className="w-full p-3 text-left rounded-lg hover:bg-slate-50 transition-colors"
                          >
                            <div className="font-medium text-slate-900">{template.name}</div>
                            <div className="text-sm text-slate-500">{template.description}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Configuration Name"
                placeholder="e.g., Dispatch Check-In v2"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              
              <Input
                label="Description"
                placeholder="Brief description of this configuration"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
              
              <Textarea
                label="System Prompt"
                placeholder="Enter the system prompt that defines the agent's behavior..."
                rows={12}
                value={formData.system_prompt}
                onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                hint="This prompt guides the agent's conversation style and objectives"
              />
              
              <Textarea
                label="Initial Message"
                placeholder="The first message the agent says when the call connects..."
                rows={3}
                value={formData.initial_message || ''}
                onChange={(e) => setFormData({ ...formData, initial_message: e.target.value })}
                hint="Use {{driver_name}} and {{load_number}} as placeholders"
              />
            </CardContent>
          </Card>

          {/* Retell AI Settings - TASK A CRITICAL */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-600" />
                <h2 className="text-lg font-semibold text-slate-900">Voice Settings</h2>
                <Badge variant="info">Retell AI</Badge>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                Configure advanced voice settings for a natural conversation experience
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <Toggle
                label="Enable Backchanneling"
                description='Agent uses acknowledgment sounds like "uh-huh", "I see", "okay" during pauses'
                checked={formData.enable_backchanneling}
                onChange={(e) => setFormData({ ...formData, enable_backchanneling: e.target.checked })}
              />
              
              <Toggle
                label="Enable Filler Words"
                description='Agent uses natural filler words like "well", "so", "let me see"'
                checked={formData.enable_filler_words}
                onChange={(e) => setFormData({ ...formData, enable_filler_words: e.target.checked })}
              />
              
              <Slider
                label="Interruption Sensitivity"
                description="How sensitive the agent is to being interrupted by the caller"
                value={formData.interruption_sensitivity}
                min={0}
                max={1}
                step={0.1}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  interruption_sensitivity: parseFloat(e.target.value) 
                })}
                valueFormatter={(v) => {
                  if (v <= 0.3) return 'Low';
                  if (v <= 0.6) return 'Medium';
                  return 'High';
                }}
              />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Saved Configurations */}
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-slate-900">Saved Configurations</h3>
            </CardHeader>
            <CardContent>
              {loadingConfigs ? (
                <div className="text-sm text-slate-500">Loading...</div>
              ) : scenarioConfigs.length === 0 ? (
                <div className="text-sm text-slate-500 text-center py-4">
                  No saved configurations yet
                </div>
              ) : (
                <div className="space-y-2">
                  {scenarioConfigs.map((config) => (
                    <button
                      key={config.id}
                      onClick={() => setSelectedConfigId(config.id)}
                      className={`w-full p-3 text-left rounded-lg transition-colors ${
                        selectedConfigId === config.id
                          ? 'bg-indigo-50 border border-indigo-200'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-slate-900">{config.name}</span>
                        {config.is_active && (
                          <Badge variant="success" size="sm">Active</Badge>
                        )}
                      </div>
                      {config.description && (
                        <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                          {config.description}
                        </p>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  setSelectedConfigId(null);
                  setFormData({
                    name: '',
                    description: '',
                    scenario_type: selectedScenario,
                    system_prompt: '',
                    initial_message: '',
                    enable_backchanneling: true,
                    enable_filler_words: true,
                    interruption_sensitivity: 0.5,
                    is_active: false,
                  });
                }}
              >
                + New Configuration
              </Button>
            </CardFooter>
          </Card>

          {/* Actions */}
          <Card>
            <CardContent className="space-y-3">
              {saveSuccess && (
                <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg text-sm">
                  <Check className="h-4 w-4" />
                  Configuration saved successfully!
                </div>
              )}
              
              <Button
                className="w-full"
                onClick={handleSave}
                isLoading={isLoading}
                leftIcon={<Save className="h-4 w-4" />}
                disabled={!formData.name || !formData.system_prompt}
              >
                {selectedConfigId ? 'Update Configuration' : 'Save Configuration'}
              </Button>
              
              {selectedConfigId && !formData.is_active && (
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={handleActivate}
                  isLoading={isActivating}
                  leftIcon={<Play className="h-4 w-4" />}
                >
                  Activate for {selectedScenario === 'dispatch_checkin' ? 'Check-In' : 'Emergency'}
                </Button>
              )}
              
              {!formData.name && (
                <div className="flex items-start gap-2 text-sm text-amber-600">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>Enter a name to save this configuration</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Current Active Config */}
          {activeConfig && (
            <Card variant="bordered">
              <CardContent>
                <div className="text-sm text-slate-600">Currently Active</div>
                <div className="font-medium text-slate-900 mt-1">{activeConfig.name}</div>
                <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                  <span>Updated {new Date(activeConfig.updated_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

