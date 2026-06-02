import React, { useState } from 'react';
import { 
    Dialog, DialogContent, DialogHeader, DialogTitle, 
    DialogDescription, DialogFooter 
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Clock, ShieldAlert, Activity, User, Send, StopCircle } from 'lucide-react';
import api from '@/lib/api';

export function LiveInterventionModal({ 
    session, 
    open, 
    onClose 
}: { 
    session: any, 
    open: boolean, 
    onClose: () => void 
}) {
    const [mode, setMode] = useState<'ai_only' | 'whisper' | 'takeover'>('ai_only');
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!session) return null;

    const handleTakeover = async (newMode: 'whisper' | 'takeover') => {
        setIsSubmitting(true);
        try {
            await api.post(`/hitl/sessions/${session.session_id}/takeover`, { mode: newMode });
            setMode(newMode);
        } catch (e) {
            console.error(e);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRelease = async () => {
        setIsSubmitting(true);
        try {
            await api.post(`/hitl/sessions/${session.session_id}/release`, {});
            setMode('ai_only');
        } catch (e) {
            console.error(e);
        } finally {
            setIsSubmitting(false);
            onClose();
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;
        
        setIsSubmitting(true);
        try {
            await api.post(`/hitl/sessions/${session.session_id}/respond`, { text: message });
            setMessage('');
        } catch (e) {
            console.error(e);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Activity className="size-5 text-red-500 animate-pulse" />
                        Live Intervention
                    </DialogTitle>
                    <DialogDescription>
                        Monitor or take over an active voice session. 
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex flex-col space-y-1">
                            <span className="text-muted-foreground text-xs font-semibold uppercase">Session ID</span>
                            <span className="font-mono text-xs">{session.session_id.substring(0, 12)}...</span>
                        </div>
                        <div className="flex flex-col space-y-1">
                            <span className="text-muted-foreground text-xs font-semibold uppercase">Caller</span>
                            <span className="flex items-center gap-1">
                                <User className="size-3" />
                                {session.caller_id || 'Unknown'}
                            </span>
                        </div>
                        <div className="flex flex-col space-y-1">
                            <span className="text-muted-foreground text-xs font-semibold uppercase">Status</span>
                            <span>
                                <Badge variant={session.status === 'escalated' ? 'destructive' : 'default'}>
                                    {session.status}
                                </Badge>
                            </span>
                        </div>
                        <div className="flex flex-col space-y-1">
                            <span className="text-muted-foreground text-xs font-semibold uppercase">Duration</span>
                            <span className="flex items-center gap-1">
                                <Clock className="size-3" />
                                {Math.floor((new Date().getTime() - new Date(session.created_at).getTime()) / 60000)} mins
                            </span>
                        </div>
                    </div>

                    <div className="border-t pt-4 mt-2">
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="text-sm font-semibold flex items-center gap-1">
                                <ShieldAlert className="size-4 text-amber-500" />
                                Takeover Mode
                            </h4>
                            <Badge variant="outline" className="font-mono">{mode}</Badge>
                        </div>
                        
                        <div className="flex gap-2">
                            <Button 
                                variant={mode === 'whisper' ? 'default' : 'outline'} 
                                onClick={() => handleTakeover('whisper')}
                                disabled={isSubmitting}
                                className="flex-1"
                            >
                                Whisper (AI Speaks)
                            </Button>
                            <Button 
                                variant={mode === 'takeover' ? 'destructive' : 'outline'} 
                                onClick={() => handleTakeover('takeover')}
                                disabled={isSubmitting}
                                className="flex-1"
                            >
                                Full Takeover
                            </Button>
                        </div>
                    </div>

                    {mode !== 'ai_only' && (
                        <form onSubmit={handleSendMessage} className="flex gap-2 mt-2">
                            <Input 
                                placeholder={mode === 'whisper' ? "Type to have AI say it..." : "Type human response..."}
                                value={message}
                                onChange={e => setMessage(e.target.value)}
                                disabled={isSubmitting}
                            />
                            <Button type="submit" disabled={isSubmitting || !message.trim()} size="icon">
                                <Send className="size-4" />
                            </Button>
                        </form>
                    )}
                </div>

                <DialogFooter>
                    {mode !== 'ai_only' ? (
                        <Button variant="outline" onClick={handleRelease} disabled={isSubmitting} className="w-full text-red-500 border-red-200 hover:bg-red-50">
                            <StopCircle className="size-4 mr-2" />
                            Release to AI
                        </Button>
                    ) : (
                        <Button variant="secondary" onClick={onClose} disabled={isSubmitting} className="w-full">
                            Close
                        </Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
