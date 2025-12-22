/**
 * Dashboard Page
 * 
 * Overview of the AI Voice Agent system showing:
 * - Active configurations
 * - Recent calls
 * - Quick actions
 */

import { Link } from 'react-router-dom';
import { 
  Settings, 
  Phone, 
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Radio,
} from 'lucide-react';
import { Card, CardHeader, CardContent, Button, Badge } from '@/components/ui';
import { useConfigs } from '@/hooks/useConfigs';

export function DashboardPage() {
  const { data: configs, isLoading } = useConfigs();

  const activeDispatch = configs?.find(
    (c) => c.scenario_type === 'dispatch_checkin' && c.is_active
  );
  const activeEmergency = configs?.find(
    (c) => c.scenario_type === 'emergency' && c.is_active
  );

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-14 h-14 bg-white/20 rounded-xl">
            <Radio className="h-7 w-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">AI Voice Agent Dashboard</h1>
            <p className="text-indigo-200 mt-1">
              Configure, test, and review calls from your AI dispatch agent
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to="/config" className="block">
          <Card className="h-full hover:shadow-md transition-shadow cursor-pointer group">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-xl">
                    <Settings className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Configure Agent</h2>
                    <p className="text-slate-500 mt-1">
                      Set up prompts and voice settings
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-indigo-600 transition-colors" />
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/calls" className="block">
          <Card className="h-full hover:shadow-md transition-shadow cursor-pointer group">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-xl">
                    <Phone className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Start Test Call</h2>
                    <p className="text-slate-500 mt-1">
                      Trigger a call and view results
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-green-600 transition-colors" />
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Active Configurations */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Active Configurations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Dispatch Check-In */}
          <Card variant="bordered">
            <CardHeader>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600">Dispatch Check-In</span>
                {activeDispatch ? (
                  <Badge variant="success">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                ) : (
                  <Badge variant="warning">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Not Configured
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {activeDispatch ? (
                <div>
                  <div className="font-medium text-slate-900">{activeDispatch.name}</div>
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                    {activeDispatch.description || 'No description'}
                  </p>
                  <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Updated {new Date(activeDispatch.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-slate-500 mb-4">No active configuration</p>
                  <Link to="/config">
                    <Button variant="outline" size="sm">Configure Now</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Emergency Protocol */}
          <Card variant="bordered">
            <CardHeader>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600">Emergency Protocol</span>
                {activeEmergency ? (
                  <Badge variant="success">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                ) : (
                  <Badge variant="warning">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Not Configured
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {activeEmergency ? (
                <div>
                  <div className="font-medium text-slate-900">{activeEmergency.name}</div>
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                    {activeEmergency.description || 'No description'}
                  </p>
                  <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Updated {new Date(activeEmergency.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-slate-500 mb-4">No active configuration</p>
                  <Link to="/config">
                    <Button variant="outline" size="sm">Configure Now</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Voice Settings Summary */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-slate-900">Voice Settings Overview</h2>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-slate-500">Loading...</div>
          ) : !activeDispatch && !activeEmergency ? (
            <div className="text-center py-6 text-slate-500">
              Configure an agent to see voice settings
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-8">
              <div>
                <div className="text-sm text-slate-600 mb-1">Backchanneling</div>
                <div className="font-medium text-slate-900">
                  {(activeDispatch?.enable_backchanneling ?? activeEmergency?.enable_backchanneling) 
                    ? 'Enabled' 
                    : 'Disabled'
                  }
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 mb-1">Filler Words</div>
                <div className="font-medium text-slate-900">
                  {(activeDispatch?.enable_filler_words ?? activeEmergency?.enable_filler_words) 
                    ? 'Enabled' 
                    : 'Disabled'
                  }
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 mb-1">Interruption Sensitivity</div>
                <div className="font-medium text-slate-900">
                  {(() => {
                    const sensitivity = activeDispatch?.interruption_sensitivity 
                      ?? activeEmergency?.interruption_sensitivity 
                      ?? 0.5;
                    if (sensitivity <= 0.3) return 'Low';
                    if (sensitivity <= 0.6) return 'Medium';
                    return 'High';
                  })()}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

