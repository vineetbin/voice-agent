/**
 * Calls Page
 * 
 * Allows administrators to:
 * - Trigger test calls (phone or web)
 * - View call status in real-time
 * - See call results with transcript and structured summary
 */

import { useState, useEffect } from 'react';
import { 
  Phone, 
  Globe, 
  Play, 
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  User,
  Truck,
  Hash,
  MessageSquare,
  FileText,
  PhoneOff,
  Mic,
  MicOff,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  Button,
  Input,
  Badge,
} from '@/components/ui';
import { useTriggerCall, useCall, useRecentCalls } from '@/hooks/useCalls';
import { useConfigs } from '@/hooks/useConfigs';
import { useRetellWebCall } from '@/hooks/useRetellWebCall';
import type { ScenarioType, CallType, CallTriggerResponse, CallWithDetails } from '@/types';

// =============================================================================
// Call Trigger Form
// =============================================================================

interface TriggerFormData {
  driverName: string;
  phoneNumber: string;
  loadNumber: string;
  scenarioType: ScenarioType;
  callType: CallType;
}

export function CallsPage() {
  const [formData, setFormData] = useState<TriggerFormData>({
    driverName: '',
    phoneNumber: '',
    loadNumber: '',
    scenarioType: 'dispatch_checkin',
    callType: 'web', // Default to web for non-USA testing
  });
  
  const [activeCall, setActiveCall] = useState<CallTriggerResponse | null>(null);
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  
  // Hooks
  const { data: configs } = useConfigs();
  const triggerMutation = useTriggerCall();
  const { data: activeCallDetails, isLoading: loadingCallDetails } = useCall(
    activeCall?.call_id || selectedCallId || undefined
  );
  const { data: recentCalls, isLoading: loadingRecent } = useRecentCalls(5);
  
  // Web call hook for browser-based calling
  const { state: webCallState, startCall: startWebCall, endCall: endWebCall, toggleMute } = useRetellWebCall();
  
  // Check if we have active configs for each scenario
  const hasDispatchConfig = configs?.some(
    (c) => c.scenario_type === 'dispatch_checkin' && c.is_active
  );
  const hasEmergencyConfig = configs?.some(
    (c) => c.scenario_type === 'emergency' && c.is_active
  );
  
  // Auto-start web call when we get an access token
  useEffect(() => {
    if (activeCall?.access_token && activeCall.call_type === 'web' && webCallState.status === 'idle') {
      startWebCall(activeCall.access_token);
    }
  }, [activeCall?.access_token, activeCall?.call_type, webCallState.status, startWebCall]);
  
  const handleTriggerCall = async () => {
    try {
      const result = await triggerMutation.mutateAsync({
        driver_name: formData.driverName,
        phone_number: formData.callType === 'phone' ? formData.phoneNumber : undefined,
        load_number: formData.loadNumber,
        scenario_type: formData.scenarioType,
        call_type: formData.callType,
      });
      
      setActiveCall(result);
      setSelectedCallId(null);
    } catch (error) {
      console.error('Failed to trigger call:', error);
    }
  };
  
  const handleEndCall = () => {
    endWebCall();
    // Clear active call after a short delay to allow state update
    setTimeout(() => setActiveCall(null), 500);
  };
  
  const isWebCallActive = webCallState.status === 'connecting' || webCallState.status === 'connected';
  
  const canTrigger = 
    formData.driverName.trim() && 
    formData.loadNumber.trim() &&
    (formData.callType === 'web' || formData.phoneNumber.trim()) &&
    (formData.scenarioType === 'dispatch_checkin' ? hasDispatchConfig : hasEmergencyConfig) &&
    !isWebCallActive;
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="default"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case 'in_progress':
        return <Badge variant="info"><Loader2 className="h-3 w-3 mr-1 animate-spin" />In Progress</Badge>;
      case 'completed':
        return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'failed':
        return <Badge variant="error"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Test Calls</h1>
        <p className="text-slate-600 mt-1">
          Trigger test calls and view results
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Trigger Form */}
        <div className="space-y-6">
          {/* Call Trigger Form */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Phone className="h-5 w-5 text-slate-600" />
                <h2 className="text-lg font-semibold text-slate-900">Start Test Call</h2>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Scenario Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scenario Type
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setFormData({ ...formData, scenarioType: 'dispatch_checkin' })}
                    className={`flex-1 p-3 rounded-lg border-2 transition-all text-sm ${
                      formData.scenarioType === 'dispatch_checkin'
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="font-medium">Dispatch Check-In</div>
                    {!hasDispatchConfig && (
                      <div className="text-xs text-amber-600 mt-1">No active config</div>
                    )}
                  </button>
                  <button
                    onClick={() => setFormData({ ...formData, scenarioType: 'emergency' })}
                    className={`flex-1 p-3 rounded-lg border-2 transition-all text-sm ${
                      formData.scenarioType === 'emergency'
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="font-medium">Emergency</div>
                    {!hasEmergencyConfig && (
                      <div className="text-xs text-amber-600 mt-1">No active config</div>
                    )}
                  </button>
                </div>
              </div>
              
              {/* Call Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Call Type
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setFormData({ ...formData, callType: 'web' })}
                    className={`flex-1 p-3 rounded-lg border-2 transition-all text-sm flex items-center justify-center gap-2 ${
                      formData.callType === 'web'
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <Globe className="h-4 w-4" />
                    <span>Web Call</span>
                  </button>
                  <button
                    onClick={() => setFormData({ ...formData, callType: 'phone' })}
                    className={`flex-1 p-3 rounded-lg border-2 transition-all text-sm flex items-center justify-center gap-2 ${
                      formData.callType === 'phone'
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <Phone className="h-4 w-4" />
                    <span>Phone Call</span>
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  {formData.callType === 'web' 
                    ? 'Web call opens in browser (recommended for non-USA testing)'
                    : 'Phone call requires a valid phone number'
                  }
                </p>
              </div>
              
              {/* Driver Name */}
              <Input
                label="Driver Name"
                placeholder="e.g., Mike Johnson"
                value={formData.driverName}
                onChange={(e) => setFormData({ ...formData, driverName: e.target.value })}
              />
              
              {/* Phone Number (only for phone calls) */}
              {formData.callType === 'phone' && (
                <Input
                  label="Phone Number"
                  placeholder="+1 555 123 4567"
                  value={formData.phoneNumber}
                  onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                  hint="E.164 format recommended"
                />
              )}
              
              {/* Load Number */}
              <Input
                label="Load Number"
                placeholder="e.g., 7891-B"
                value={formData.loadNumber}
                onChange={(e) => setFormData({ ...formData, loadNumber: e.target.value })}
              />
            </CardContent>
            <CardFooter>
              <Button
                className="w-full"
                onClick={handleTriggerCall}
                isLoading={triggerMutation.isPending}
                disabled={!canTrigger}
                leftIcon={<Play className="h-4 w-4" />}
              >
                Start Test Call
              </Button>
            </CardFooter>
          </Card>

          {/* Recent Calls */}
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-slate-900">Recent Calls</h3>
            </CardHeader>
            <CardContent>
              {loadingRecent ? (
                <div className="text-sm text-slate-500">Loading...</div>
              ) : !recentCalls?.length ? (
                <div className="text-sm text-slate-500 text-center py-4">
                  No calls yet. Trigger your first test call above!
                </div>
              ) : (
                <div className="space-y-2">
                  {recentCalls.map((call) => (
                    <button
                      key={call.id}
                      onClick={() => {
                        setSelectedCallId(call.id);
                        setActiveCall(null);
                      }}
                      className={`w-full p-3 text-left rounded-lg transition-colors ${
                        selectedCallId === call.id
                          ? 'bg-indigo-50 border border-indigo-200'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-slate-400" />
                          <span className="font-medium text-slate-900">{call.driver_name}</span>
                        </div>
                        {getStatusBadge(call.status)}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Truck className="h-3 w-3" />
                          {call.load_number}
                        </span>
                        {call.duration_seconds && (
                          <span>{Math.floor(call.duration_seconds / 60)}:{(call.duration_seconds % 60).toString().padStart(2, '0')}</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Call Results */}
        <div className="space-y-6">
          {/* Active Call Status */}
          {activeCall && (
            <Card variant="bordered">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900">Active Call</h3>
                  {activeCallDetails && getStatusBadge(activeCallDetails.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Hash className="h-4 w-4 text-slate-400" />
                    <span className="text-slate-600">Call ID:</span>
                    <code className="text-xs bg-slate-100 px-2 py-0.5 rounded">
                      {activeCall.retell_call_id}
                    </code>
                  </div>
                  
                  {/* Web Call Status and Controls */}
                  {activeCall.call_type === 'web' && (
                    <div className="space-y-3">
                      {/* Connection Status */}
                      <div className={`p-3 rounded-lg text-sm ${
                        webCallState.status === 'connected' 
                          ? 'bg-green-50 text-green-800'
                          : webCallState.status === 'connecting'
                          ? 'bg-amber-50 text-amber-800'
                          : webCallState.status === 'error'
                          ? 'bg-red-50 text-red-800'
                          : 'bg-slate-50 text-slate-800'
                      }`}>
                        <p className="font-medium">
                          {webCallState.status === 'idle' && 'Initializing...'}
                          {webCallState.status === 'connecting' && 'Connecting to call...'}
                          {webCallState.status === 'connected' && '🎙️ Call Connected - Speak now!'}
                          {webCallState.status === 'ended' && 'Call Ended'}
                          {webCallState.status === 'error' && `Error: ${webCallState.error}`}
                        </p>
                        {webCallState.status === 'connected' && (
                          <p className="text-xs mt-1">
                            Your microphone is active. Speak to interact with the agent.
                          </p>
                        )}
                      </div>
                      
                      {/* Call Controls */}
                      {webCallState.status === 'connected' && (
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={toggleMute}
                            leftIcon={webCallState.isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                          >
                            {webCallState.isMuted ? 'Unmute' : 'Mute'}
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={handleEndCall}
                            leftIcon={<PhoneOff className="h-4 w-4" />}
                          >
                            End Call
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {activeCallDetails?.status === 'in_progress' && activeCall.call_type === 'phone' && (
                    <div className="flex items-center gap-2 text-sm text-indigo-600">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Phone call in progress... Auto-refreshing every 3 seconds</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Call Results */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-slate-600" />
                <h2 className="text-lg font-semibold text-slate-900">Call Results</h2>
              </div>
            </CardHeader>
            <CardContent>
              {loadingCallDetails ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                </div>
              ) : !activeCallDetails && !selectedCallId ? (
                <div className="text-center py-8 text-slate-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No call selected</p>
                  <p className="text-sm">Trigger a call or select from recent calls</p>
                </div>
              ) : activeCallDetails ? (
                <CallResultsDisplay call={activeCallDetails} />
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Call Results Display Component
// =============================================================================

interface CallResultsDisplayProps {
  call: CallWithDetails;
}

function CallResultsDisplay({ call }: CallResultsDisplayProps) {
  const [showTranscript, setShowTranscript] = useState(false);

  return (
    <div className="space-y-4">
      {/* Call Metadata */}
      <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
        <div>
          <div className="text-xs text-slate-500">Driver</div>
          <div className="font-medium text-slate-900">{call.driver_name}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Load</div>
          <div className="font-medium text-slate-900">{call.load_number}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Duration</div>
          <div className="font-medium text-slate-900">
            {call.duration_seconds 
              ? `${Math.floor(call.duration_seconds / 60)}:${(call.duration_seconds % 60).toString().padStart(2, '0')}`
              : 'N/A'
            }
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Type</div>
          <div className="font-medium text-slate-900 capitalize">{call.call_type}</div>
        </div>
      </div>

      {/* Structured Summary */}
      {call.structured_summary ? (
        <div>
          <h4 className="font-medium text-slate-900 mb-2">Structured Summary</h4>
          <div className="space-y-2">
            <SummaryRow label="Call Outcome" value={call.structured_summary.call_outcome} />
            <SummaryRow label="Driver Status" value={call.structured_summary.driver_status} />
            <SummaryRow label="Current Location" value={call.structured_summary.current_location} />
            <SummaryRow label="ETA" value={call.structured_summary.eta} />
            <SummaryRow label="Delay Reason" value={call.structured_summary.delay_reason} />
            <SummaryRow label="Unloading Status" value={call.structured_summary.unloading_status} />
            <SummaryRow label="POD Acknowledged" value={call.structured_summary.pod_reminder_acknowledged} />
            <SummaryRow label="Emergency Type" value={call.structured_summary.emergency_type} />
            <SummaryRow label="Safety Status" value={call.structured_summary.safety_status} />
            <SummaryRow label="Injury Status" value={call.structured_summary.injury_status} />
            <SummaryRow label="Emergency Location" value={call.structured_summary.emergency_location} />
            <SummaryRow label="Load Secure" value={call.structured_summary.load_secure} />
            <SummaryRow label="Escalation Status" value={call.structured_summary.escalation_status} />
          </div>
        </div>
      ) : call.status === 'completed' ? (
        <div className="p-4 bg-amber-50 rounded-lg text-sm text-amber-800">
          <p className="font-medium">Summary Pending</p>
          <p className="text-xs mt-1">
            Structured summary will be available after post-processing.
          </p>
        </div>
      ) : null}

      {/* Transcript */}
      {call.transcript && (
        <div>
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            className="flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            <MessageSquare className="h-4 w-4" />
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </button>
          
          {showTranscript && (
            <div className="mt-3 p-4 bg-slate-50 rounded-lg max-h-96 overflow-y-auto">
              {call.transcript.utterances?.length ? (
                <div className="space-y-3">
                  {call.transcript.utterances.map((utterance, idx) => (
                    <div key={idx} className={`flex gap-3 ${utterance.role === 'agent' ? '' : 'flex-row-reverse'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        utterance.role === 'agent' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-600'
                      }`}>
                        {utterance.role === 'agent' ? 'A' : 'D'}
                      </div>
                      <div className={`flex-1 p-3 rounded-lg ${
                        utterance.role === 'agent' ? 'bg-indigo-50' : 'bg-white border border-slate-200'
                      }`}>
                        <div className="text-xs text-slate-500 mb-1 capitalize">{utterance.role}</div>
                        <div className="text-sm text-slate-900">{utterance.content}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <pre className="text-sm text-slate-700 whitespace-pre-wrap">
                  {call.transcript.raw_transcript || 'No transcript available'}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper component for summary rows
function SummaryRow({ label, value }: { label: string; value: string | boolean | null | undefined }) {
  // Skip null/undefined values
  if (value === null || value === undefined) {
    return null;
  }
  
  const displayValue = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);
  
  return (
    <div className="flex justify-between py-2 border-b border-slate-100">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="text-sm font-medium text-slate-900">{displayValue}</span>
    </div>
  );
}

