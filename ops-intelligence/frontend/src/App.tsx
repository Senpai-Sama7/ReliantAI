import { useState } from 'react'
import Layout from './components/Layout'
import IncidentPanel from './components/panels/IncidentPanel'
import DebtROIPanel from './components/panels/DebtROIPanel'
import CloudCostPanel from './components/panels/CloudCostPanel'
import PipelinePanel from './components/panels/PipelinePanel'
import PerformancePanel from './components/panels/PerformancePanel'
import MigrationPanel from './components/panels/MigrationPanel'
import APIGovernancePanel from './components/panels/APIGovernancePanel'
import RevenuePanel from './components/panels/RevenuePanel'

const PANELS: Record<string, JSX.Element> = {
  revenue:     <RevenuePanel />,
  incidents:   <IncidentPanel />,
  debt:        <DebtROIPanel />,
  costs:       <CloudCostPanel />,
  pipelines:   <PipelinePanel />,
  performance: <PerformancePanel />,
  migrations:  <MigrationPanel />,
  api:         <APIGovernancePanel />,
}

export default function App() {
  const [active, setActive] = useState('revenue')
  return (
    <Layout active={active} onNav={setActive}>
      {PANELS[active]}
    </Layout>
  )
}
