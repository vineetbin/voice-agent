/**
 * Agent Configuration Page
 * 
 * Single unified configuration that handles both dispatch check-in and emergency scenarios.
 * The agent automatically handles both flows based on the conversation context.
 * 
 * Sync behavior:
 * - On load: Loads the single active configuration
 * - On save: Updates both DB and Retell
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Save, 
  FileText, 
  Sparkles,
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
  useRetellConfig,
} from '@/hooks/useConfigs';
import { configsApi } from '@/services/api';
import type { AgentConfigCreate } from '@/types';

export function ConfigurationPage() {
  // Form state - single unified config (uses dispatch_checkin internally)
  const [formData, setFormData] = useState<AgentConfigCreate>({
    name: '',
    description: '',
    scenario_type: 'dispatch_checkin', // Internal default, not shown in UI
    system_prompt: '',
    initial_message: '',
    enable_backchanneling: true,
    enable_filler_words: true,
    interruption_sensitivity: 0.5,
    is_active: false,
  });
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // API hooks
  const { data: configs, refetch: refetchConfigs } = useConfigs();
  const createMutation = useCreateConfig();
  const updateMutation = useUpdateConfig();
  
  // Retell config (for display and sync check)
  const { data: retellConfig, isLoading: loadingRetell, refetch: refetchRetell } = useRetellConfig();

  // Get the single active config
  const activeConfig = configs?.find((c) => c.is_active);

  // Check if form has unsaved changes compared to Retell
  const hasRetellDiff = retellConfig && activeConfig && (
    retellConfig.general_prompt !== activeConfig.system_prompt ||
    retellConfig.begin_message !== activeConfig.initial_message ||
    retellConfig.enable_backchannel !== activeConfig.enable_backchanneling ||
    Math.abs(retellConfig.interruption_sensitivity - activeConfig.interruption_sensitivity) > 0.01
  );

  // Sync from Retell - updates/creates the unified config with Retell's current values
  const handleSyncFromRetell = useCallback(async () => {
    if (!retellConfig) return;
    
    setIsSyncing(true);
    try {
      // Use scenario_type from active config, or default to first available
      const syncScenarioType = activeConfig?.scenario_type || 'dispatch_checkin';
      const synced = await configsApi.syncFromRetell(syncScenarioType);
      
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
      
      // Refetch configs
      await refetchConfigs();
    } catch (error) {
      console.error('Failed to sync from Retell:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [retellConfig, refetchConfigs]);

  // Load active config into form on mount
  useEffect(() => {
    if (activeConfig) {
      setFormData({
        name: activeConfig.name,
        description: activeConfig.description || '',
        scenario_type: activeConfig.scenario_type,
        system_prompt: activeConfig.system_prompt,
        initial_message: activeConfig.initial_message || '',
        enable_backchanneling: activeConfig.enable_backchanneling,
        enable_filler_words: activeConfig.enable_filler_words,
        interruption_sensitivity: activeConfig.interruption_sensitivity,
        is_active: activeConfig.is_active,
      });
    }
  }, [activeConfig]);



  // Save configuration (saves to DB, and if active, also pushes to Retell)
  const handleSave = async () => {
    try {
      if (activeConfig) {
        await updateMutation.mutateAsync({
          id: activeConfig.id,
          data: formData,
        });
      } else {
        const newConfig = { ...formData, is_active: true };
        await createMutation.mutateAsync(newConfig);
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

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Agent Configuration</h1>
          <p className="text-slate-600 mt-1">
            Configure prompts and voice settings. The agent handles both dispatch check-in and emergency scenarios automatically.
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
          {/* Prompt Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-slate-600" />
                <h2 className="text-lg font-semibold text-slate-900">Prompt Configuration</h2>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Configuration Name"
                placeholder="e.g., Unified Agent Configuration"
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
                placeholder="Enter the system prompt that defines the agent's behavior for both dispatch check-in and emergency scenarios..."
                rows={14}
                value={formData.system_prompt}
                onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                hint="This prompt should handle both normal check-ins and emergency situations. The agent will automatically pivot based on the conversation context."
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
                variant="primary"
                onClick={handleSave}
                isLoading={isLoading}
                leftIcon={saveSuccess ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
              >
                {saveSuccess ? 'Saved!' : 'Save & Sync to Retell'}
              </Button>
              
              {formData.is_active && (
                <div className="p-3 bg-green-50 rounded-lg text-sm text-green-800">
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4" />
                    <span className="font-medium">Active Configuration</span>
                  </div>
                  <p className="text-xs mt-1">
                    Changes will be pushed to Retell when you save.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Config Info */}
          {activeConfig && (
            <Card variant="bordered">
              <CardContent>
                <div className="text-sm text-slate-600 mb-2">Active Configuration</div>
                <div className="font-medium text-slate-900 text-lg">{activeConfig.name}</div>
                {activeConfig.description && (
                  <div className="text-sm text-slate-600 mt-2">{activeConfig.description}</div>
                )}
                <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
                  <span>Last updated {new Date(activeConfig.updated_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
