//! Reinforcement Learning agent for the Autonomous Adaptive Expert System (AAES).
//!
//! This agent leverages the Julia compute engine to train and evaluate a
//! policy on the CartPole environment.  It exposes methods to
//! perform training, evaluation and automated improvement until a
//! target reward is achieved.  Training and inference are executed
//! through the `JuliaBridge` defined in `julia_bridge.rs`.

use crate::julia_bridge::JuliaBridge;
use anyhow::Result;

/// An agent that trains and evaluates a CartPole policy via Julia.
pub struct RlAgent {
    julia: JuliaBridge,
}

impl RlAgent {
    /// Construct a new RL agent from an existing Julia runtime handle.
    pub fn new(julia: JuliaBridge) -> Self {
        Self { julia }
    }

    /// Train the policy for the specified number of episodes.  The
    /// current policy is loaded from disk if it exists and saved
    /// after training.  Returns the cumulative reward obtained.
    pub fn train(&self, episodes: i64) -> Result<()> {
        println!("🤖 RL Agent training for {} episodes...", episodes);
        let reward = self.julia.train_cartpole(episodes)?;
        println!("✅ RL Training complete. Total Reward: {:.2}", reward);
        Ok(())
    }

    /// Evaluate the current policy without further training.  Returns
    /// the total reward collected over the given number of episodes.
    pub fn evaluate(&self, episodes: i64) -> Result<()> {
        println!("📊 Evaluating trained policy...");
        let reward = self.julia.evaluate_cartpole(episodes)?;
        println!("📈 Avg Reward ({} episodes): {:.2}", episodes, reward);
        Ok(())
    }

    /// Automatically improve the policy until it reaches the target
    /// reward.  The agent alternates between training and evaluation
    /// loops, reporting progress after each iteration.  This method
    /// blocks until the target is met or an error occurs.
    pub fn auto_improve(&self, target_reward: f64) -> Result<()> {
        let mut current = self.julia.evaluate_cartpole(5)?;
        while current < target_reward {
            println!("🔄 Improving policy... Current Reward: {:.2}", current);
            self.julia.train_cartpole(20)?;
            current = self.julia.evaluate_cartpole(5)?;
        }
        println!("🏆 Target Reward Reached: {:.2}", current);
        Ok(())
    }
}