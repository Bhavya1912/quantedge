"""
QuantEdge Backend Test Suite
Tests for Black-Scholes, EV engine, Monte Carlo, payoff calculator.
Run: pytest tests/backend/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

import numpy as np
import pytest

from core.black_scholes import bs_price, bs_greeks, implied_volatility
from core.payoff import compute_multi_leg_payoff, compute_payoff_curve, net_premium_collected
from core.ev_engine import compute_true_ev, compute_pop_exact
from core.monte_carlo import box_muller_normal, simulate_gbm_paths, run_monte_carlo


# ── Black-Scholes Tests ──────────────────────────────────────────────────────

class TestBlackScholes:

    def test_call_put_parity(self):
        """Put-call parity: C - P = S - K·e^(-rT)"""
        S, K, T, r, sigma = 100, 100, 0.25, 0.06, 0.20
        call = bs_price(S, K, T, r, sigma, "call")
        put = bs_price(S, K, T, r, sigma, "put")
        parity = S - K * np.exp(-r * T)
        assert abs((call - put) - parity) < 0.01, f"PCP violated: {call-put:.4f} vs {parity:.4f}"

    def test_atm_call_price_reasonable(self):
        """ATM call should be roughly 0.4×σ×S×√T (Brenner-Subrahmanyam)"""
        S, K, T, r, sigma = 51200, 51200, 1/365, 0.065, 0.143
        call = bs_price(S, K, T, r, sigma, "call")
        approx = 0.4 * sigma * S * np.sqrt(T)
        assert 0.5 * approx < call < 2.0 * approx

    def test_deep_itm_call_delta(self):
        """Deep ITM call should have delta near 1."""
        greeks = bs_greeks(200, 100, 1.0, 0.06, 0.20, "call")
        assert greeks["delta"] > 0.99

    def test_deep_otm_call_delta(self):
        """Deep OTM call should have delta near 0."""
        greeks = bs_greeks(100, 200, 1.0, 0.06, 0.20, "call")
        assert greeks["delta"] < 0.01

    def test_gamma_positive(self):
        """Gamma is always positive for both calls and puts."""
        for opt_type in ["call", "put"]:
            g = bs_greeks(100, 100, 0.25, 0.06, 0.20, opt_type)
            assert g["gamma"] > 0

    def test_vega_positive(self):
        """Vega is always positive (long options gain value with vol)."""
        for opt_type in ["call", "put"]:
            g = bs_greeks(100, 100, 0.25, 0.06, 0.20, opt_type)
            assert g["vega"] > 0

    def test_theta_negative_long(self):
        """Theta is negative for long options (time decay hurts buyers)."""
        for opt_type in ["call", "put"]:
            g = bs_greeks(100, 100, 0.25, 0.06, 0.20, opt_type)
            assert g["theta"] < 0, f"Theta should be negative for long {opt_type}"

    def test_implied_volatility_recovery(self):
        """IV recovery: BS(IV) should return original IV."""
        S, K, T, r = 51200, 51200, 1/365, 0.065
        true_iv = 0.1432
        price = bs_price(S, K, T, r, true_iv, "call")
        recovered_iv = implied_volatility(price, S, K, T, r, "call")
        assert abs(recovered_iv - true_iv) < 0.001, f"IV recovery: {recovered_iv:.4f} vs {true_iv:.4f}"

    def test_zero_time_intrinsic(self):
        """At expiry, option value = intrinsic value."""
        assert abs(bs_price(110, 100, 0, 0.06, 0.20, "call") - 10) < 0.01
        assert abs(bs_price(90, 100, 0, 0.06, 0.20, "put") - 10) < 0.01
        assert bs_price(90, 100, 0, 0.06, 0.20, "call") == 0.0


# ── Payoff Calculator Tests ──────────────────────────────────────────────────

class TestPayoff:

    def setup_method(self):
        """Bull Call Spread: +51000CE / -51200CE, premium = 254 - 124 = 130 debit"""
        self.bull_call_legs = [
            {"K": 51000, "option_type": "call", "position": "long",  "quantity": 1, "premium": 254},
            {"K": 51200, "option_type": "call", "position": "short", "quantity": 1, "premium": 124},
        ]

    def test_bull_call_below_lower_strike_max_loss(self):
        """Below lower strike: max loss = net debit paid."""
        pnl = compute_multi_leg_payoff(self.bull_call_legs, ST=50500, lot_size=1)
        assert abs(pnl - (-130)) < 1, f"Expected -130, got {pnl}"

    def test_bull_call_above_upper_strike_max_profit(self):
        """Above upper strike: max profit = spread width - debit."""
        pnl = compute_multi_leg_payoff(self.bull_call_legs, ST=51500, lot_size=1)
        assert abs(pnl - 70) < 1, f"Expected 70, got {pnl}"  # (200 - 130)

    def test_bull_call_breakeven(self):
        """Breakeven at lower strike + net debit."""
        expected_be = 51000 + 130  # = 51130
        pnl_at_be = compute_multi_leg_payoff(self.bull_call_legs, ST=expected_be, lot_size=1)
        assert abs(pnl_at_be) < 2, f"P&L at breakeven should be ~0, got {pnl_at_be}"

    def test_net_premium_debit(self):
        """Net premium for bull call spread is negative (debit)."""
        net_prem = net_premium_collected(self.bull_call_legs)
        assert net_prem == -130  # Pay 254, receive 124

    def test_breakeven_detection(self):
        """Payoff curve should detect breakeven points."""
        curve = compute_payoff_curve(self.bull_call_legs, S0=51100, price_range_pct=0.10, n_points=500, lot_size=1)
        assert len(curve["breakevens"]) >= 1

    def test_iron_condor_max_loss(self):
        """Iron condor: max loss = wing width - premium received."""
        ic_legs = [
            {"K": 50600, "option_type": "put",  "position": "long",  "quantity": 1, "premium": 20},
            {"K": 50800, "option_type": "put",  "position": "short", "quantity": 1, "premium": 64},
            {"K": 51400, "option_type": "call", "position": "short", "quantity": 1, "premium": 52},
            {"K": 51600, "option_type": "call", "position": "long",  "quantity": 1, "premium": 18},
        ]
        # Far below: put spread max loss
        pnl_down = compute_multi_leg_payoff(ic_legs, ST=50000, lot_size=1)
        # Far above: call spread max loss
        pnl_up = compute_multi_leg_payoff(ic_legs, ST=52000, lot_size=1)
        # Both should be losses
        assert pnl_down < 0 and pnl_up < 0


# ── EV Engine Tests ──────────────────────────────────────────────────────────

class TestEVEngine:

    def setup_method(self):
        self.bull_call_legs = [
            {"K": 51000, "option_type": "call", "position": "long",  "quantity": 1, "premium": 254},
            {"K": 51200, "option_type": "call", "position": "short", "quantity": 1, "premium": 124},
        ]

    def test_ev_returns_dict(self):
        result = compute_true_ev(
            legs=self.bull_call_legs, S0=51200, sigma=0.143, T=1/365, r=0.065
        )
        assert isinstance(result, dict)
        for key in ["ev", "pop", "max_loss", "max_profit", "sharpe"]:
            assert key in result

    def test_pop_between_0_and_1(self):
        result = compute_true_ev(
            legs=self.bull_call_legs, S0=51200, sigma=0.143, T=1/365, r=0.065
        )
        assert 0 <= result["pop"] <= 1

    def test_max_loss_negative(self):
        """Bull call spread max loss should be negative."""
        result = compute_true_ev(
            legs=self.bull_call_legs, S0=51200, sigma=0.143, T=1/365, r=0.065
        )
        assert result["max_loss"] < 0

    def test_exact_pop_cdf(self):
        """POP from CDF should be between 0 and 1."""
        pop = compute_pop_exact(51200, 51080, 0.143, 1/365, 0.065, "above")
        assert 0 < pop < 1

    def test_pop_atm_near_50pct(self):
        """ATM POP for very short expiry should be near 50%."""
        # For extremely short T, ATM option POP ≈ 50%
        pop = compute_pop_exact(51200, 51200, 0.143, 1e-5, 0.065, "above")
        assert 0.45 < pop < 0.55


# ── Monte Carlo Tests ────────────────────────────────────────────────────────

class TestMonteCarlo:

    def test_box_muller_mean_near_zero(self):
        """Box-Muller samples should have mean ≈ 0."""
        Z = box_muller_normal(100000, seed=42)
        assert abs(np.mean(Z)) < 0.01

    def test_box_muller_std_near_one(self):
        """Box-Muller samples should have std ≈ 1."""
        Z = box_muller_normal(100000, seed=42)
        assert abs(np.std(Z) - 1.0) < 0.01

    def test_box_muller_no_clipping(self):
        """Box-Muller should produce values beyond ±1.5 unlike CLT approx."""
        Z = box_muller_normal(100000, seed=42)
        assert np.any(np.abs(Z) > 3.0)

    def test_gbm_positive_prices(self):
        """GBM paths must always be positive."""
        paths = simulate_gbm_paths(100, 0.065, 0.20, 1/365, n_simulations=1000, seed=42)
        assert np.all(paths > 0)

    def test_gbm_initial_price(self):
        """All paths start at S0."""
        S0 = 51204
        paths = simulate_gbm_paths(S0, 0.065, 0.143, 1/365, n_simulations=1000, seed=42)
        assert np.all(paths[:, 0] == S0)

    def test_mc_ev_positive_for_itm(self):
        """Deep ITM call should have positive MC EV."""
        legs = [{"K": 50000, "option_type": "call", "position": "long",
                 "quantity": 1, "premium": 100}]
        result = run_monte_carlo(legs, S0=51200, sigma=0.143, T=1/365, r=0.065,
                                  n_simulations=5000, seed=42, lot_size=1)
        # Deep ITM call should profit
        assert result["ev"] > 0

    def test_mc_histogram_sums_to_1(self):
        """Histogram frequency should sum close to 1."""
        legs = [{"K": 51200, "option_type": "call", "position": "long",
                 "quantity": 1, "premium": 124}]
        result = run_monte_carlo(legs, S0=51200, sigma=0.143, T=1/365, r=0.065,
                                  n_simulations=5000, seed=42, lot_size=1)
        total_freq = sum(b["frequency"] for b in result["histogram"])
        assert abs(total_freq - 1.0) < 0.02


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
