import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from '../components/AppShell';
import HomeScreen from '../pages/HomeScreen';
import DataScreen from '../pages/DataScreen';
import AnalyticsScreen from '../pages/AnalyticsScreen';
import ChatHistoryScreen from '../pages/ChatHistoryScreen';
import ProfileSettingsScreen from '../pages/ProfileSettingsScreen';
import CustomersPage from '../pages/data/CustomersPage';
import InventoryPage from '../pages/data/InventoryPage';
import ExpensesPage from '../pages/data/ExpensesPage';
import SalesPage from '../pages/data/SalesPage';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/data" element={<DataScreen />} />
          <Route path="/data/customers" element={<CustomersPage />} />
          <Route path="/data/inventory" element={<InventoryPage />} />
          <Route path="/data/expenses" element={<ExpensesPage />} />
          <Route path="/data/sales" element={<SalesPage />} />
          <Route path="/analytics" element={<AnalyticsScreen />} />
          <Route path="/history" element={<ChatHistoryScreen />} />
          <Route path="/profile" element={<ProfileSettingsScreen />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
