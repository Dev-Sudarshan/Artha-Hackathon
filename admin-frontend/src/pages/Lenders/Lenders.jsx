import React, { useState, useEffect } from 'react';
import { getLenders } from '../../services/adminApi';

const Lenders = () => {
  const [lenders, setLenders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLenders();
  }, []);

  const loadLenders = async () => {
    try {
      const data = await getLenders();
      setLenders(data.items || []);
    } catch (err) {
      console.error('Failed to load lenders', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading lenders...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1>Lenders Management</h1>
      <p>Total Lenders: {lenders.length}</p>
      {/* Lender list will be displayed here */}
    </div>
  );
};

export default Lenders;
