import React from 'react';
import { Link } from 'react-router-dom';
import { Auth } from '../services/auth';

const UnauthorizedPage = () => {
  const user = Auth.user;

  return (
    <div className="min-h-screen bg-[#EBF5FB] flex items-center justify-center px-6" style={{ fontFamily: 'Inter, sans-serif' }}>
      <div className="w-full max-w-xl bg-white rounded-[48px] p-12 border border-[#D5D8DC] shadow-xl">
        <div className="text-[10px] font-black uppercase tracking-widest text-[#566573]">Access</div>
        <h1 className="text-4xl font-black text-[#0D1B2A] mt-3">Unauthorized</h1>
        <p className="text-sm font-bold text-[#566573] mt-4">
          Your account role doesn’t have access to this portal.
        </p>

        <div className="mt-8 space-y-3">
          <Link
            to={user ? Auth.redirectPath(user.role) : '/signin'}
            className="block text-center w-full py-4 rounded-2xl font-black text-white bg-[#1B4F72] hover:bg-[#2471A3] transition-all"
          >
            Go to my portal
          </Link>
          <Link
            to="/signin"
            className="block text-center w-full py-4 rounded-2xl font-black text-[#0D1B2A] bg-[#EBF5FB] border border-[#D5D8DC] hover:bg-white transition-all"
          >
            Sign in with another account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default UnauthorizedPage;

