import React, { useState, useEffect } from 'react';
import { getBorrowers } from '../../services/adminApi';

const Borrowers = () => {
  const [borrowers, setBorrowers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBorrowers();
  }, []);

  const loadBorrowers = async () => {
    try {
      const data = await getBorrowers();
      setBorrowers(data.items || []);
    } catch (err) {
      console.error('Failed to load borrowers', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading borrowers...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1>Borrowers Management</h1>
      <p>Total Borrowers: {borrowers.length}</p>
      {/* Borrower list will be displayed here */}
    </div>
  );
};

export default Borrowers;
