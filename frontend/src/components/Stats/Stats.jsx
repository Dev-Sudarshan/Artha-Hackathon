import './Stats.css';

const Stats = () => {
    const stats = [
        { label: 'Active Members', value: '10,000+' },
        { label: 'Total Loans', value: 'NPR 50M+' },
        { label: 'Repayment Rate', value: '95%' },
        { label: 'Lives Impacted', value: '7,500+' },
    ];

    return (
        <section className="stats-section">
            <div className="container">
                <div className="stats-grid animate-slide-up">
                    {stats.map((stat, index) => (
                        <div key={index} className="stat-card">
                            <h3 className="stat-value">{stat.value}</h3>
                            <p className="stat-label">{stat.label}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Stats;
