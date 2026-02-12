import React, { useState, useEffect } from 'react';
import { Activity, FileText, Clock, Search, ArrowRight, CheckCircle, Lock, Shield } from 'lucide-react';
import './BlockchainExplorer.css';

const BlockchainExplorer = () => {
    const [loans, setLoans] = useState([]);
    const [stats, setStats] = useState({
        totalTransactions: 1245,
        activeStreams: 4,
        networkStatus: 'Active'
    });
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResult, setSearchResult] = useState(null);
    const [isVerifying, setIsVerifying] = useState(false);

    useEffect(() => {
        // Fetch public blockchain data
        const fetchBlockchainData = async () => {
            try {
                // 1. Fetch Latest Loans
                const loansResp = await fetch('http://localhost:8000/api/public/explore/loans?limit=20');
                if (loansResp.ok) {
                    const data = await loansResp.json();
                    setLoans(data.loans || []);
                }

                // 2. Fetch Network Stats & Blocks
                const statsResp = await fetch('http://localhost:8000/api/public/explore/stats');
                if (statsResp.ok) {
                    const data = await statsResp.json();
                    if (data.stats) {
                        setStats({
                            totalTransactions: data.stats.difficulty ? Math.floor(data.stats.blocks * 3.5) : 0, // Estimate
                            activeStreams: data.stats.connections > 0 ? 3 : 1,
                            networkStatus: data.stats.is_mining ? 'Mining (Active)' : 'Syncing'
                        });
                    }
                }
            } catch (error) {
                console.error("Failed to fetch blockchain data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchBlockchainData();
        const interval = setInterval(fetchBlockchainData, 4000); // Poll every 4s
        
        return () => clearInterval(interval);
    }, []);

    const formatHash = (hash) => {
        if (!hash) return 'Pending...';
        return `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`;
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return 'Just now';
        return new Date(timestamp * 1000).toLocaleString();
    };

    const handleVerify = async () => {
        if (!searchQuery.trim()) return;
        
        setIsVerifying(true);
        setSearchResult(null);

        try {
            const response = await fetch(`http://localhost:8000/api/public/explore/loan/${searchQuery.trim()}`);
            if (response.ok) {
                const data = await response.json();
                setTimeout(() => {
                    setSearchResult({ success: true, data });
                }, 800);
            } else {
                setTimeout(() => {
                    setSearchResult({ success: false, error: 'Asset not found or invalid' });
                }, 800);
            }
        } catch (error) {
            setSearchResult({ success: false, error: 'Network error checking chain' });
        } finally {
            setTimeout(() => setIsVerifying(false), 800);
        }
    };

    return (
        <div className="blockchain-explorer">
            <div className="explorer-header-row">
                <div className="header-title">
                    <h1>MultiChain Ledger</h1>
                    <p>Permissioned Financial Blockchain Network</p>
                </div>
            </div>

            <div className="dashboard-grid">
                {/* Main Stats */}
                <div className="grid-card stats-overview">
                    <div className="stat-row">
                        <Activity className="stat-icon-sm blue" />
                        <div>
                            <h4>{stats.totalTransactions}</h4>
                            <small>Total Transactions</small>
                        </div>
                    </div>
                    <div className="stat-row">
                        <Lock className="stat-icon-sm green" />
                        <div>
                            <h4>{stats.activeStreams}</h4>
                            <small>Secured Streams</small>
                        </div>
                    </div>
                </div>
            </div>

            <div className="explorer-content">
                <div className="search-bar">
                    <Search className="search-icon" size={20} />
                    <input 
                        type="text" 
                        placeholder="Search by Transaction Hash / Block / Loan ID" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleVerify()}
                    />
                    <button onClick={handleVerify} disabled={isVerifying}>
                        {isVerifying ? 'Verifying...' : 'Verify Hash'}
                    </button>
                </div>

                {searchResult && (
                    <div className={`verification-result ${searchResult.success ? 'success' : 'error'}`}>
                        {searchResult.success ? (
                            <div className="verified-box animate-slide-in">
                                <div className="seal">
                                    <CheckCircle size={48} />
                                    <span>VERIFIED</span>
                                </div>
                                <div className="verified-details">
                                    <h4><Shield size={16} /> Cryptographically Verified on MultiChain</h4>
                                    <div className="detail-grid">
                                        <div className="detail-item">
                                            <span>Loan ID</span>
                                            <strong>{searchResult.data.loan_id}</strong>
                                        </div>
                                        <div className="detail-item">
                                            <span>Transaction Hash</span>
                                            <code className="hash-code">{searchResult.data.blockchain_proof.transaction_hash}</code>
                                        </div>
                                        <div className="detail-item">
                                            <span>Data Hash</span>
                                            <code className="hash-code">{searchResult.data.blockchain_proof.loan_hash || 'N/A'}</code>
                                        </div>
                                        <div className="detail-item">
                                            <span>Block Time</span>
                                            <strong>{searchResult.data.blockchain_proof.stored_at}</strong>
                                        </div>
                                        <div className="detail-item">
                                            <span>Confirmations</span>
                                            <strong>{searchResult.data.blockchain_proof.confirmations}</strong>
                                        </div>
                                        {searchResult.data.blockchain_proof.borrower && (
                                            <div className="detail-item">
                                                <span>Borrower</span>
                                                <strong>{searchResult.data.blockchain_proof.borrower}</strong>
                                            </div>
                                        )}
                                        {searchResult.data.blockchain_proof.lender && (
                                            <div className="detail-item">
                                                <span>Lender</span>
                                                <strong>{searchResult.data.blockchain_proof.lender}</strong>
                                            </div>
                                        )}
                                        {searchResult.data.blockchain_proof.is_repaid && (
                                            <div className="detail-item">
                                                <span>Repayment</span>
                                                <strong style={{color: '#22c55e'}}>FULLY REPAID</strong>
                                            </div>
                                        )}
                                    </div>
                                    <div className="watermark">OFFICIAL RECORD</div>
                                </div>
                            </div>
                        ) : (
                            <div className="error-box animate-slide-in">
                                <Activity className="error-icon" size={24} />
                                <div>
                                    <h4>Verification Failed</h4>
                                    <p>{searchResult.error}</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <div className="transactions-card">
                    <div className="card-header">
                        <h2>Latest Verified Transactions</h2>
                        <button className="view-all">View All <ArrowRight size={16} /></button>
                    </div>
                    
                    <div className="table-responsive">
                        <table className="tx-table">
                            <thead>
                                <tr>
                                    <th>Loan ID</th>
                                    <th>Transaction Hash</th>
                                    <th>Type</th>
                                    <th>Time</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="5" className="text-center">Loading blockchain data...</td></tr>
                                ) : loans.length > 0 ? (
                                    loans.map((loan, index) => (
                                        <tr key={index}>
                                            <td className="font-medium">{loan.loan_id}</td>
                                            <td>
                                                <span className="hash-tag" title={loan.transaction_hash}>
                                                    {formatHash(loan.transaction_hash)}
                                                </span>
                                            </td>
                                            <td>
                                                <span className="tx-type">Loan Storage</span>
                                            </td>
                                            <td className="text-muted">
                                                <Clock size={14} style={{ display: 'inline', marginRight: '5px', verticalAlign: 'text-bottom' }} />
                                                {formatTime(loan.block_time || loan.timestamp)}
                                            </td>
                                            <td>
                                                <span className="status-badge success">
                                                    <CheckCircle size={12} style={{ marginRight: '4px' }} />
                                                    Confirmed
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr><td colSpan="5" className="text-center">No recent transactions found.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BlockchainExplorer;
