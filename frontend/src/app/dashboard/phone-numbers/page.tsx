'use client';

import { useState, useEffect } from 'react';
import { Phone, Plus, Search, Globe, Loader2, CheckCircle2, XCircle, ShoppingCart, Trash2, RefreshCw, PhoneOff } from 'lucide-react';
import { searchAvailableNumbers, purchasePhoneNumber, fetchOwnedNumbers, releasePhoneNumber, syncPhoneNumbers } from '@/lib/api';
import { AvailablePhoneNumber, PhoneNumberInfo } from '@/types/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function PhoneNumbersPage() {
    const [owned, setOwned] = useState<PhoneNumberInfo[]>([]);
    const [available, setAvailable] = useState<AvailablePhoneNumber[]>([]);
    const [loading, setLoading] = useState(false);
    const [searching, setSearching] = useState(false);
    const [purchasing, setPurchasing] = useState<string | null>(null);
    const [releasing, setReleasing] = useState<string | null>(null);
    const [syncing, setSyncing] = useState(false);
    const [searchForm, setSearchForm] = useState({ country_code: 'IN', area_code: '', contains: '' });
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const loadOwned = async () => {
        setLoading(true);
        try {
            const data = await fetchOwnedNumbers();
            setOwned(data.numbers || []);
        } catch (err) {
            console.error('Failed to load phone numbers:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadOwned(); }, []);

    const handleSearch = async () => {
        setSearching(true);
        try {
            const data = await searchAvailableNumbers({
                country_code: searchForm.country_code,
                area_code: searchForm.area_code || undefined,
                contains: searchForm.contains || undefined,
                limit: 10,
            });
            setAvailable(data.results || []);
        } catch (err) {
            setToastMessage('Failed to search numbers');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setSearching(false);
        }
    };

    const handlePurchase = async (number: AvailablePhoneNumber) => {
        setPurchasing(number.phone_number);
        try {
            await purchasePhoneNumber({ phone_number: number.phone_number });
            setAvailable(prev => prev.filter(n => n.phone_number !== number.phone_number));
            setToastMessage(`Purchased ${number.phone_number}`);
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
            await loadOwned();
        } catch (err: any) {
            setToastMessage(err.message || 'Purchase failed');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setPurchasing(null);
        }
    };

    const handleRelease = async (id: string) => {
        setReleasing(id);
        try {
            await releasePhoneNumber(id);
            setToastMessage('Number released');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
            await loadOwned();
        } catch (err: any) {
            setToastMessage(err.message || 'Release failed');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setReleasing(null);
        }
    };

    const handleSync = async () => {
        setSyncing(true);
        try {
            const result = await syncPhoneNumbers();
            setToastMessage(`Synced ${result.synced} numbers from Twilio`);
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
            await loadOwned();
        } catch (err: any) {
            setToastMessage(err.message || 'Sync failed');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setSyncing(false);
        }
    };

    const capBadge = (cap: { voice: boolean; sms: boolean; mms: boolean }, key: string) => {
        const on = cap[key as keyof typeof cap];
        return (
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase ${on ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'}`}>
                {key}
            </span>
        );
    };

    return (
        <div className="space-y-6 pb-10">
            {showToast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 bg-green-500/10 border border-green-500/30 backdrop-blur-xl rounded-2xl shadow-xl text-green-600 dark:text-green-400 text-sm font-semibold transition-all duration-300 animate-in fade-in">
                    <CheckCircle2 className="size-5 text-green-500" />
                    <span>{toastMessage}</span>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-foreground">
                        Phone <span className="text-primary font-semibold">Numbers</span>
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">Provision and manage your Twilio phone numbers.</p>
                </div>
                <Button type="button" onClick={handleSync} disabled={syncing} variant="outline" className="gap-2 text-xs">
                    <RefreshCw className={`size-3 ${syncing ? 'animate-spin' : ''}`} />
                    {syncing ? 'Syncing...' : 'Sync from Twilio'}
                </Button>
            </div>

            {/* Owned Numbers */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Phone className="size-4 text-primary" />
                        Your Numbers
                        {owned.length > 0 && (
                            <span className="text-xs font-normal text-muted-foreground ml-1">({owned.length})</span>
                        )}
                    </CardTitle>
                    <CardDescription className="text-xs">
                        Phone numbers assigned to your workspace.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="size-5 animate-spin text-muted-foreground" />
                        </div>
                    ) : owned.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center bg-muted/40 rounded-2xl border border-dashed border-border">
                            <PhoneOff className="size-10 text-muted-foreground mb-3" />
                            <h4 className="text-xs font-semibold text-foreground">No phone numbers yet</h4>
                            <p className="text-[10px] text-muted-foreground mt-1 max-w-xs">Search for available numbers below and purchase one to get started.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {owned.map((num) => (
                                <div key={num.id} className="flex items-center justify-between p-4 bg-muted/30 border border-border rounded-xl hover:border-primary/20 transition-all">
                                    <div className="flex items-center gap-4 min-w-0">
                                        <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                            <Phone className="size-4" />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="text-sm font-semibold text-foreground font-mono">{num.phone_number}</p>
                                            {num.friendly_name && (
                                                <p className="text-[10px] text-muted-foreground truncate">{num.friendly_name}</p>
                                            )}
                                            <div className="flex items-center gap-1.5 mt-1">
                                                {capBadge(num.capabilities, 'voice')}
                                                {capBadge(num.capabilities, 'sms')}
                                                {capBadge(num.capabilities, 'mms')}
                                                {num.region && (
                                                    <span className="text-[9px] text-muted-foreground ml-1">{num.region}</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleRelease(num.id)}
                                        disabled={releasing === num.id}
                                        className="text-red-500 hover:text-red-600 hover:bg-red-500/10 shrink-0"
                                    >
                                        {releasing === num.id ? <Loader2 className="size-3 animate-spin" /> : <Trash2 className="size-3.5" />}
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Search Available Numbers */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Search className="size-4 text-primary" />
                        Search Available Numbers
                    </CardTitle>
                    <CardDescription className="text-xs">
                        Find and purchase phone numbers from Twilio.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="space-y-1.5">
                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Country</Label>
                            <select
                                value={searchForm.country_code}
                                onChange={e => setSearchForm({ ...searchForm, country_code: e.target.value })}
                                className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                                <option value="IN">India (+91)</option>
                                <option value="US">United States (+1)</option>
                                <option value="GB">United Kingdom (+44)</option>
                                <option value="CA">Canada (+1)</option>
                                <option value="AU">Australia (+61)</option>
                                <option value="SG">Singapore (+65)</option>
                                <option value="DE">Germany (+49)</option>
                                <option value="FR">France (+33)</option>
                            </select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Area Code</Label>
                            <Input
                                value={searchForm.area_code}
                                onChange={e => setSearchForm({ ...searchForm, area_code: e.target.value })}
                                placeholder="e.g. 22"
                                className="text-xs"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Contains</Label>
                            <Input
                                value={searchForm.contains}
                                onChange={e => setSearchForm({ ...searchForm, contains: e.target.value })}
                                placeholder="e.g. 9876"
                                className="text-xs"
                            />
                        </div>
                        <div className="space-y-1.5 flex items-end">
                            <Button type="button" onClick={handleSearch} disabled={searching} className="w-full gap-2 text-xs">
                                {searching ? <Loader2 className="size-3 animate-spin" /> : <Search className="size-3" />}
                                {searching ? 'Searching...' : 'Search'}
                            </Button>
                        </div>
                    </div>

                    {/* Results */}
                    {available.length > 0 && (
                        <div className="space-y-2 mt-4 pt-4 border-t border-border">
                            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{available.length} numbers available</p>
                            {available.map((num) => (
                                <div key={num.phone_number} className="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-xl hover:border-primary/20 transition-all">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <Globe className="size-4 text-muted-foreground shrink-0" />
                                        <div className="min-w-0">
                                            <p className="text-xs font-semibold text-foreground font-mono">{num.phone_number}</p>
                                            <p className="text-[9px] text-muted-foreground">
                                                {[num.locality, num.region].filter(Boolean).join(', ') || '—'}
                                            </p>
                                            <div className="flex items-center gap-1 mt-1">
                                                {capBadge(num.capabilities, 'voice')}
                                                {capBadge(num.capabilities, 'sms')}
                                                {capBadge(num.capabilities, 'mms')}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 shrink-0">
                                        {num.price && (
                                            <span className="text-xs font-semibold text-muted-foreground">{num.price}/mo</span>
                                        )}
                                        <Button
                                            type="button"
                                            size="sm"
                                            onClick={() => handlePurchase(num)}
                                            disabled={purchasing === num.phone_number}
                                            className="gap-1.5 text-xs"
                                        >
                                            {purchasing === num.phone_number ? (
                                                <Loader2 className="size-3 animate-spin" />
                                            ) : (
                                                <ShoppingCart className="size-3" />
                                            )}
                                            {purchasing === num.phone_number ? 'Buying...' : 'Buy'}
                                        </Button>
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
