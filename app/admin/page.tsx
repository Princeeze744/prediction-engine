import Link from 'next/link';
export default function Admin(){return <main className="wrap">
 <div className="page-title"><span>Private</span><h1>Control room</h1><p>Nothing to paste any more. The daily run pulls every fixture and price from the API, builds the free picks and the 10 VIP tickets, and settles yesterday’s results.</p></div>
 <div className="history-table">
  <div className="history-row"><span><b>Run today’s update</b><small>PowerShell, in the v22 folder</small></span><span style={{gridColumn:'2/-1'}}><code>&amp; ".\tools\QS_Daily_Run.ps1"</code></span></div>
  <div className="history-row"><span><b>Model lab</b><small>All 30 models and ticket records</small></span><span style={{gridColumn:'2/-1'}}><Link href="/admin/models" className="ghost-link">Open</Link></span></div>
  <div className="history-row"><span><b>No-draw research</b><small>Paper test of the data-gap signal</small></span><span style={{gridColumn:'2/-1'}}><Link href="/admin/research" className="ghost-link">Open</Link></span></div>
 </div></main>}
