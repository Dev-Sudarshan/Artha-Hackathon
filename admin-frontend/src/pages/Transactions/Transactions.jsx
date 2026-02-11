import React, { useState, useEffect } from 'react';
import { getTransactions } from '../../services/adminApi';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      const data = await getTransactions();
      setTransactions(data.items || []);
    } catch (err) {
      console.error('Failed to load transactions', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading transactions...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1>Transaction Analysis</h1>
      <p>Total Transactions: {transactions.length}</p>
      {/* Transaction list will be displayed here */}
    </div>
  );
};

export default Transactions;
