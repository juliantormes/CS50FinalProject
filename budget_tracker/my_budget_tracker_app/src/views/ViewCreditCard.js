import React from 'react';
import Header from '../components/Header';
import SidebarMenu from '../components/SidebarMenu';
import { useAuth } from '../hooks/useAuth';

const ViewCreditCard = () => {
  const { logout } = useAuth();

  return (
    <div className="view-credit-card">
      <div className="sidebar-container">
        <SidebarMenu />
      </div>
      <div className="content">
        <Header logout={logout} />
        <h1>View Credit Card</h1>
        {/* Add your content here */}
      </div>
    </div>
  );
};

export default ViewCreditCard;
