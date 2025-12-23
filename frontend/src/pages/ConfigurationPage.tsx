/**
 * Agent Configuration Page
 * 
 * Allows administrators to:
 * - Select scenario type (Dispatch Check-In, Emergency)
 * - Edit system prompts and initial messages
 * - Configure Retell AI settings (Task A requirements)
 * - Load preset templates
 * - Save and activate configurations
 * 
 * Sync behavior:
 * - On load: Compares DB config with Retell, updates DB if Retell has changes
 * - On save (active config): Updates both DB and Retell
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Settings, 
  Save, 
  Play, 
  FileText, 
  Sparkles,
  ChevronDown,
  Check,
  AlertCircle,
  RefreshCw,
  Cloud,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardContent,
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
  useActivateConfig,
  useRetellConfig,
} from '@/hooks/useConfigs';
import { configsApi } from '@/services/api';
import { getTemplatesForScenario } from '@/services/templates';
import type { AgentConfigCreate, ScenarioType, PromptTemplate } from '@/types';

// Scenario options
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
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'synced' | 'error'>('idle');

  // API hooks
  const { data: configs, isLoading: loadingConfigs, refetch: refetchConfigs } = useConfigs();
  const createMutation = useCreateConfig();
  const updateMutation = useUpdateConfig();
  const activateMutation = useActivateConfig();
  
  // Retell config (for display and sync check)
  const { data: retellConfig, isLoading: loadingRetell, refetch: refetchRetell } = useRetellConfig();

  // Get configs for current scenario
  const scenarioConfigs = configs?.filter((c) => c.scenario_type === selectedScenario) || [];
  const activeConfig = scenarioConfigs.find((c) => c.is_active);

  // Get templates for current scenario
  const availableTemplates = getTemplatesForScenario(selectedScenario);

  // Check if form has unsaved changes compared to Retell
  const hasRetellDiff = retellConfig && activeConfig && (
    retellConfig.general_prompt !== activeConfig.system_prompt ||
    retellConfig.begin_message !== activeConfig.initial_message ||
    retellConfig.enable_backchannel !== activeConfig.enable_backchanneling ||
    Math.abs(retellConfig.interruption_sensitivity - activeConfig.interruption_sensitivity) > 0.01
  );

  // Sync from Retell - updates the active config in DB with Retell's current values
  const handleSyncFromRetell = useCallback(async () => {
    if (!retellConfig) return;
    
    setIsSyncing(true);
    try {
      // Sync and get the updated config
      const synced = await configsApi.syncFromRetell(selectedScenario);
      
      // Load into form
      setFormData({
        name: synced.name,
        description: synced.description || '',
        scenario_type: synced.scenario_type,
        system_prompt: synced.system_prompt,
        initial_message: synced.initial_message || '',
        enable_backchanneling: synced.enable_backchanneling,
        enable_filler_words: synced.enable_filler_words,
        interruption_sensitivity: synced.interruption_sensitivity,
        is_active: synced.is_active,
      });
      setSelectedConfigId(synced.id);
      
      // Refetch configs
      await refetchConfigs();
      setSyncStatus('synced');
      setTimeout(() => setSyncStatus('idle'), 3000);
    } catch (error) {
      console.error('Failed to sync from Retell:', error);
      setSyncStatus('error');
    } finally {
      setIsSyncing(false);
    }
  }, [retellConfig, selectedScenario, refetchConfigs]);

  // Auto-sync on load if there's a difference between Retell and active config
  useEffect(() => {
    if (hasRetellDiff && !isSyncing && syncStatus === 'idle') {
      // There's a diff - show indicator but don't auto-sync (let user decide)
    }
  }, [hasRetellDiff, isSyncing, syncStatus]);

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

  // Load active config when scenario changes
  useEffect(() => {
    if (activeConfig && !selectedConfigId) {
      setSelectedConfigId(activeConfig.id);
    }
  }, [activeConfig, selectedConfigId]);

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

  // Save configuration (saves to DB, and if active, also pushes to Retell)
  const handleSave = async () => {
    try {
      let savedConfig;
      
      if (selectedConfigId) {
        savedConfig = await updateMutation.mutateAsync({
          id: selectedConfigId,
          data: formData,
        });
      } else {
        savedConfig = await createMutation.mutateAsync(formData);
        setSelectedConfigId(savedConfig.id);
      }
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      
      // Refetch to get latest
      await refetchConfigs();
      await refetchRetell();
    } catch (error) {
      console.error('Failed to save:', error);
    }
  };

  // Activate configuration (marks as active in DB and pushes to Retell)
  const handleActivate = async () => {
    if (selectedConfigId) {
      await activateMutation.mutateAsync(selectedConfigId);
      await refetchConfigs();
      await refetchRetell();
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const isActivating = activateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Agent Configuration</h1>
          <p className="text-slate-600 mt-1">
            Configure prompts and voice settings for your AI agent
          </p>
        </div>
        
        {/* Retell Sync Status */}
        <div className="flex items-center gap-3">
          {loadingRetell ? (
            <span className="text-sm text-slate-500">Checking Retell...</span>
          ) : retellConfig ? (
            <div className="flex items-center gap-2">
              {hasRetellDiff ? (
                <>
                  <Badge variant="warning" size="sm">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Retell has changes
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSyncFromRetell}
                    isLoading={isSyncing}
                    leftIcon={<RefreshCw className="h-4 w-4" />}
                  >
                    Pull from Retell
                  </Button>
                </>
              ) : (
                <Badge variant="success" size="sm">
                  <Cloud className="h-3 w-3 mr-1" />
                  Synced with Retell
                </Badge>
              )}
            </div>
          ) : (
            <Badge variant="error" size="sm">Retell not connected</Badge>
          )}
        </div>
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

          {/* Voice Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-slate-600" />
                <h2 className="text-lg font-semibold text-slate-900">Voice Settings</h2>
                <Badge variant="default" size="sm">Retell AI</Badge>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                Configure advanced voice settings for a natural conversation experience
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Backchanneling */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-900">Backchanneling</div>
                  <div className="text-sm text-slate-500">
                    Use acknowledgment sounds like "uh-huh", "I see"
                  </div>
                </div>
                <Toggle
                  checked={formData.enable_backchanneling}
                  onChange={(e) => setFormData({ ...formData, enable_backchanneling: e.target.checked })}
                />
              </div>

              {/* Filler Words */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-900">Filler Words</div>
                  <div className="text-sm text-slate-500">
                    Use natural filler words like "um", "well"
                  </div>
                </div>
                <Toggle
                  checked={formData.enable_filler_words}
                  onChange={(e) => setFormData({ ...formData, enable_filler_words: e.target.checked })}
                />
              </div>

              {/* Interruption Sensitivity */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-medium text-slate-900">Interruption Sensitivity</div>
                    <div className="text-sm text-slate-500">
                      How quickly the agent responds to interruptions
                    </div>
                  </div>
                  <span className="text-sm font-medium text-slate-700">
                    {Math.round((formData.interruption_sensitivity ?? 0.5) * 100)}%
                  </span>
                </div>
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  value={formData.interruption_sensitivity ?? 0.5}
                  onChange={(e) => setFormData({ ...formData, interruption_sensitivity: parseFloat(e.target.value) })}
                  showValue={false}
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>Less sensitive</span>
                  <span>More sensitive</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Save Card */}
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-slate-900">Actions</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                className="w-full"
                variant="outline"
                onClick={handleSave}
                isLoading={isLoading}
                leftIcon={saveSuccess ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
              >
                {saveSuccess ? 'Saved!' : (selectedConfigId ? 'Update Configuration' : 'Save Configuration')}
              </Button>
              
              {selectedConfigId && !formData.is_active && (
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={handleActivate}
                  isLoading={isActivating}
                  leftIcon={<Play className="h-4 w-4" />}
                >
                  Activate & Push to Retell
                </Button>
              )}
              
              {formData.is_active && (
                <div className="p-3 bg-green-50 rounded-lg text-sm text-green-800">
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4" />
                    <span className="font-medium">Currently Active</span>
                  </div>
                  <p className="text-xs mt-1">
                    Changes will be pushed to Retell when you save.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Existing Configs */}
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-slate-900">Saved Configurations</h3>
            </CardHeader>
            <CardContent>
              {loadingConfigs ? (
                <div className="text-sm text-slate-500">Loading...</div>
              ) : scenarioConfigs.length === 0 ? (
                <div className="text-sm text-slate-500 text-center py-4">
                  No configurations saved for this scenario yet.
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
                        <div className="text-sm text-slate-500 mt-1 truncate">
                          {config.description}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Configuration Info */}
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
