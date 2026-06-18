import Link from 'next/link';
import DashboardLayout from '../../components/DashboardLayout';
import DeploymentsList from '../../components/DeploymentsList';

export default function DeploymentsPage() {
  return (
    <DashboardLayout
      title="Deployments"
      subtitle="Monitor and manage site deployments in real time"
      actions={
        <Link
          href="/deployments/create"
          className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-semibold hover:bg-purple-700"
        >
          + New Deployment
        </Link>
      }
    >
      <DeploymentsList showFilters />
    </DashboardLayout>
  );
}
