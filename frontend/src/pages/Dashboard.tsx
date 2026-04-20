import { ThreatStatusBanner } from '../components/dashboard/ThreatStatusBanner';
import { MetricCard } from '../components/dashboard/MetricCard';
import { LiveThreatChart } from '../components/dashboard/LiveThreatChart';
import { AttackTypeDistribution } from '../components/dashboard/AttackTypeDistribution';
import { RecentAlertsPanel } from '../components/dashboard/RecentAlertsPanel';
import { ModelAgreementPanel } from '../components/dashboard/ModelAgreementPanel';
import { useAegisStore } from '../store/useAegisStore';

export default function Dashboard() {
    const { eventsPerMinute, threatRatePercent, activeAttackTypes, events } = useAegisStore();

    const mttd = eventsPerMinute > 0 ? (60 / eventsPerMinute).toFixed(3) : '0.000';

    return (
        <div className="p-6 h-full flex flex-col space-y-6 overflow-auto">
            <ThreatStatusBanner />

            <div className="grid grid-cols-5 gap-4">
                <MetricCard title="Events / Min" value={eventsPerMinute} trend="neutral" />
                <MetricCard title="Threat Rate" value={threatRatePercent} subtitle="Percent of traffic flagged" type={threatRatePercent > 10 ? 'threat' : 'default'} />
                <MetricCard title="Active Threats" value={activeAttackTypes.length || 0} type={activeAttackTypes.length > 0 ? "threat" : "default"} />
                <MetricCard title="Model Confidence" value={events.length > 0 ? events[0].confidence * 100 : 0} subtitle="Avg % on latest prediction" type="primary" />
                <MetricCard title="MTTD" value={`${mttd}s`} subtitle="Mean Time To Detect" />
            </div>

            <LiveThreatChart />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 min-h-[300px]">
                <AttackTypeDistribution />
                <RecentAlertsPanel />
                <ModelAgreementPanel />
            </div>
        </div>
    );
}
