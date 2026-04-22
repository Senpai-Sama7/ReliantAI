//! Real-time WebSocket API for live communication

use anyhow::{anyhow, Result};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime};
use tokio::sync::{RwLock, mpsc, broadcast};
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use futures_util::{StreamExt, SinkExt};
use dashmap::DashMap;
use tracing::{info, error, instrument, debug};

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Query,
    },
    http::StatusCode,
    response::IntoResponse,
};
use axum_extra::extract::cookie::CookieJar;

/// WebSocket connection information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSocketConnection {
    pub connection_id: Uuid,
    pub user_id: Option<String>,
    pub session_id: Option<String>,
    pub connected_at: SystemTime,
    pub last_activity: SystemTime,
    pub client_info: ClientInfo,
    pub subscriptions: Vec<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientInfo {
    pub user_agent: Option<String>,
    pub ip_address: String,
    pub platform: Option<String>,
    pub version: Option<String>,
}

/// WebSocket message types
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload")]
pub enum WebSocketMessage {
    // Connection management
    Connect(ConnectPayload),
    Disconnect(DisconnectPayload),
    Ping(PingPayload),
    Pong(PongPayload),
    
    // Subscription management
    Subscribe(SubscribePayload),
    Unsubscribe(UnsubscribePayload),
    
    // Agent communication
    AgentRequest(AgentRequestPayload),
    AgentResponse(AgentResponsePayload),
    AgentStatus(AgentStatusPayload),
    
    // Real-time events
    TaskUpdate(TaskUpdatePayload),
    MetricsUpdate(MetricsUpdatePayload),
    AlertNotification(AlertPayload),
    
    // Collaboration
    BroadcastMessage(BroadcastPayload),
    DirectMessage(DirectMessagePayload),
    
    // Error handling
    Error(ErrorPayload),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectPayload {
    pub client_info: ClientInfo,
    pub auth_token: Option<String>,
    pub session_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisconnectPayload {
    pub reason: String,
    pub code: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PingPayload {
    pub timestamp: u64,
    pub sequence: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PongPayload {
    pub timestamp: u64,
    pub sequence: u64,
    pub latency_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscribePayload {
    pub channels: Vec<String>,
    pub filters: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnsubscribePayload {
    pub channels: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRequestPayload {
    pub request_id: Uuid,
    pub agent_name: String,
    pub input: serde_json::Value,
    pub stream_response: bool,
    pub timeout_seconds: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentResponsePayload {
    pub request_id: Uuid,
    pub success: bool,
    pub response: Option<serde_json::Value>,
    pub error: Option<String>,
    pub partial: bool,
    pub final_response: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentStatusPayload {
    pub agent_name: String,
    pub status: String,
    pub health: serde_json::Value,
    pub metrics: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskUpdatePayload {
    pub task_id: Uuid,
    pub status: String,
    pub progress: f64,
    pub message: Option<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsUpdatePayload {
    pub metric_name: String,
    pub value: f64,
    pub timestamp: u64,
    pub labels: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertPayload {
    pub alert_id: Uuid,
    pub severity: String,
    pub title: String,
    pub message: String,
    pub timestamp: u64,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BroadcastPayload {
    pub channel: String,
    pub message: serde_json::Value,
    pub sender_id: Option<String>,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DirectMessagePayload {
    pub recipient_id: String,
    pub message: serde_json::Value,
    pub sender_id: String,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorPayload {
    pub error_code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}

/// WebSocket server configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSocketConfig {
    pub max_connections: usize,
    pub max_message_size: usize,
    pub ping_interval_seconds: u64,
    pub connection_timeout_seconds: u64,
    pub enable_compression: bool,
    pub enable_authentication: bool,
    pub rate_limit_messages_per_minute: u32,
    pub max_subscriptions_per_connection: usize,
}

impl Default for WebSocketConfig {
    fn default() -> Self {
        Self {
            max_connections: 10_000,
            max_message_size: 1024 * 1024, // 1MB
            ping_interval_seconds: 30,
            connection_timeout_seconds: 300, // 5 minutes
            enable_compression: true,
            enable_authentication: true,
            rate_limit_messages_per_minute: 100,
            max_subscriptions_per_connection: 50,
        }
    }
}

/// Real-time WebSocket server
#[derive(Clone)]
pub struct WebSocketServer {
    config: WebSocketConfig,
    connections: Arc<DashMap<Uuid, WebSocketConnection>>,
    connection_handlers: Arc<DashMap<Uuid, mpsc::Sender<WebSocketMessage>>>,
    subscriptions: Arc<DashMap<String, Vec<Uuid>>>, // channel -> connection_ids
    message_broadcaster: broadcast::Sender<(String, WebSocketMessage)>,
    stats: Arc<RwLock<WebSocketStats>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WebSocketStats {
    pub total_connections: u64,
    pub active_connections: usize,
    pub messages_sent: u64,
    pub messages_received: u64,
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub subscription_count: usize,
    pub error_count: u64,
    pub average_latency_ms: f64,
}

impl WebSocketServer {
    /// Create a new WebSocket server
    pub fn new(config: WebSocketConfig) -> Self {
        let (message_broadcaster, _) = broadcast::channel(10_000);
        
        Self {
            config,
            connections: Arc::new(DashMap::new()),
            connection_handlers: Arc::new(DashMap::new()),
            subscriptions: Arc::new(DashMap::new()),
            message_broadcaster,
            stats: Arc::new(RwLock::new(WebSocketStats::default())),
        }
    }

    /// Start the WebSocket server
    #[instrument(skip(self))]
    pub async fn start(&self) -> Result<()> {
        info!("Starting WebSocket server");
        
        // Start background tasks
        self.start_ping_task().await;
        self.start_cleanup_task().await;
        self.start_stats_task().await;
        
        info!("WebSocket server started successfully");
        Ok(())
    }

    /// Handle WebSocket upgrade
    #[instrument(skip(self, ws))]
    pub async fn handle_upgrade(
        &self,
        ws: WebSocketUpgrade,
        query: Query<HashMap<String, String>>,
        cookies: CookieJar,
    ) -> impl IntoResponse {
        // Extract authentication info
        let auth_token: Option<String> = query.get("token")
            .cloned()
            .or_else(|| cookies.get("auth_token").map(|c| c.value().to_string()));

        // Check connection limits
        if self.connections.len() >= self.config.max_connections {
            return (StatusCode::TOO_MANY_REQUESTS, "Connection limit exceeded").into_response();
        }

        // Clone self for the async move closure
        let this = self.clone();
        // Upgrade to WebSocket
        ws.on_upgrade(move |socket| this.handle_connection(socket, auth_token))
            .into_response()
    }

    /// Handle new WebSocket connection
    async fn handle_connection(self, socket: WebSocket, _auth_token: Option<String>) {
        let connection_id = Uuid::new_v4();
        let (ws_sender, mut ws_receiver) = socket.split();
        let (msg_sender, mut msg_receiver) = mpsc::channel::<WebSocketMessage>(1000);

        // Create connection info
        let connection = WebSocketConnection {
            connection_id,
            user_id: None, // Would be set after authentication
            session_id: None,
            connected_at: SystemTime::now(),
            last_activity: SystemTime::now(),
            client_info: ClientInfo {
                user_agent: None,
                ip_address: "127.0.0.1".to_string(), // Would be extracted from headers
                platform: None,
                version: None,
            },
            subscriptions: Vec::new(),
            metadata: HashMap::new(),
        };

        // Store connection
        self.connections.insert(connection_id, connection);
        self.connection_handlers.insert(connection_id, msg_sender.clone());

        // Update stats
        {
            let mut stats = self.stats.write().await;
            stats.total_connections += 1;
            stats.active_connections = self.connections.len();
        }

        info!("New WebSocket connection established: {}", connection_id);

        // Spawn message sender task
        let ws_sender: Arc<tokio::sync::Mutex<futures_util::stream::SplitSink<WebSocket, Message>>> = Arc::new(tokio::sync::Mutex::new(ws_sender));
        let sender_task: tokio::task::JoinHandle<()> = {
            let ws_sender = ws_sender.clone();
            let stats = self.stats.clone();
            
            tokio::spawn(async move {
                while let Some(message) = msg_receiver.recv().await {
                    let json_message = match serde_json::to_string(&message) {
                        Ok(json) => json,
                        Err(e) => {
                            error!("Failed to serialize WebSocket message: {}", e);
                            continue;
                        }
                    };

                    let ws_message = Message::Text(json_message.clone());
                    
                    if let Ok(mut sender) = ws_sender.try_lock() {
                        if let Err(e) = sender.send(ws_message).await {
                            error!("Failed to send WebSocket message: {}", e);
                            break;
                        }
                        
                        // Update stats
                        let mut stats = stats.write().await;
                        stats.messages_sent += 1;
                        stats.bytes_sent += json_message.len() as u64;
                    }
                }
            })
        };

        // Handle incoming messages
        let connections: Arc<DashMap<Uuid, WebSocketConnection>> = self.connections.clone();
        let _subscriptions: Arc<DashMap<String, Vec<Uuid>>> = self.subscriptions.clone();
        let _message_broadcaster: broadcast::Sender<(String, WebSocketMessage)> = self.message_broadcaster.clone();
        let stats: Arc<RwLock<WebSocketStats>> = self.stats.clone();

        while let Some(msg) = ws_receiver.next().await as Option<std::result::Result<Message, axum::Error>> {
            match msg {
                Ok(Message::Text(text)) => {
                    // Update activity timestamp
                    if let Some(mut conn) = connections.get_mut(&connection_id) {
                        conn.last_activity = SystemTime::now();
                    }

                    // Parse and handle message
                    match serde_json::from_str::<WebSocketMessage>(&text) {
                        Ok(ws_message) => {
                            self.handle_message(connection_id, ws_message, &msg_sender).await;
                        }
                        Err(e) => {
                            error!("Failed to parse WebSocket message: {}", e);
                            let error_msg = WebSocketMessage::Error(ErrorPayload {
                                error_code: "PARSE_ERROR".to_string(),
                                message: "Invalid message format".to_string(),
                                details: None,
                            });
                            let _ = msg_sender.send(error_msg).await;
                        }
                    }

                    // Update stats
                    let mut stats = stats.write().await;
                    stats.messages_received += 1;
                    stats.bytes_received += text.len() as u64;
                }
                Ok(Message::Binary(_)) => {
                    // Handle binary messages if needed
                }
                Ok(Message::Close(_)) => {
                    info!("WebSocket connection closed: {}", connection_id);
                    break;
                }
                Ok(Message::Ping(data)) => {
                    // Respond with pong
                    if let Ok(mut sender) = ws_sender.try_lock() {
                        let _ = sender.send(Message::Pong(data)).await;
                    }
                }
                Ok(Message::Pong(_)) => {
                    // Handle pong response
                }
                Err(e) => {
                    error!("WebSocket error for connection {}: {}", connection_id, e);
                    break;
                }
            }
        }

        // Cleanup connection
        sender_task.abort();
        self.cleanup_connection(connection_id).await;
    }

    /// Handle WebSocket message
    async fn handle_message(
        &self,
        connection_id: Uuid,
        message: WebSocketMessage,
        sender: &mpsc::Sender<WebSocketMessage>,
    ) {
        match message {
            WebSocketMessage::Connect(payload) => {
                self.handle_connect(connection_id, payload, sender).await;
            }
            WebSocketMessage::Subscribe(payload) => {
                self.handle_subscribe(connection_id, payload, sender).await;
            }
            WebSocketMessage::Unsubscribe(payload) => {
                self.handle_unsubscribe(connection_id, payload).await;
            }
            WebSocketMessage::AgentRequest(payload) => {
                self.handle_agent_request(connection_id, payload, sender).await;
            }
            WebSocketMessage::BroadcastMessage(payload) => {
                self.handle_broadcast(payload).await;
            }
            WebSocketMessage::DirectMessage(payload) => {
                self.handle_direct_message(payload).await;
            }
            WebSocketMessage::Ping(payload) => {
                self.handle_ping(payload, sender).await;
            }
            _ => {
                debug!("Unhandled message type for connection: {}", connection_id);
            }
        }
    }

    /// Handle connection message
    async fn handle_connect(
        &self,
        connection_id: Uuid,
        payload: ConnectPayload,
        sender: &mpsc::Sender<WebSocketMessage>,
    ) {
        // Update connection info
        if let Some(mut conn) = self.connections.get_mut(&connection_id) {
            conn.client_info = payload.client_info;
            conn.session_id = payload.session_id;
            
            // Authenticate if token provided
            if let Some(_token) = payload.auth_token {
                // Implement authentication logic here
                conn.user_id = Some("authenticated_user".to_string());
            }
        }

        // Send confirmation
        let response = WebSocketMessage::Connect(ConnectPayload {
            client_info: ClientInfo {
                user_agent: None,
                ip_address: "server".to_string(),
                platform: Some("acropolis".to_string()),
                version: Some("1.0.0".to_string()),
            },
            auth_token: None,
            session_id: Some(connection_id.to_string()),
        });

        let _ = sender.send(response).await;
    }

    /// Handle subscription
    async fn handle_subscribe(
        &self,
        connection_id: Uuid,
        payload: SubscribePayload,
        sender: &mpsc::Sender<WebSocketMessage>,
    ) {
        let mut subscribed_channels = Vec::new();

        for channel in payload.channels {
            // Check subscription limits
            if let Some(conn) = self.connections.get(&connection_id) {
                if conn.subscriptions.len() >= self.config.max_subscriptions_per_connection {
                    let error_msg = WebSocketMessage::Error(ErrorPayload {
                        error_code: "SUBSCRIPTION_LIMIT".to_string(),
                        message: "Maximum subscriptions exceeded".to_string(),
                        details: None,
                    });
                    let _ = sender.send(error_msg).await;
                    continue;
                }
            }

            // Add subscription
            self.subscriptions
                .entry(channel.clone())
                .or_insert_with(Vec::new)
                .push(connection_id);

            // Update connection subscriptions
            if let Some(mut conn) = self.connections.get_mut(&connection_id) {
                conn.subscriptions.push(channel.clone());
            }

            subscribed_channels.push(channel);
        }

        // Send confirmation
        let response = WebSocketMessage::Subscribe(SubscribePayload {
            channels: subscribed_channels,
            filters: payload.filters,
        });

        let _ = sender.send(response).await;
    }

    /// Handle unsubscription
    async fn handle_unsubscribe(&self, connection_id: Uuid, payload: UnsubscribePayload) {
        for channel in payload.channels {
            // Remove from channel subscriptions
            if let Some(mut subscribers) = self.subscriptions.get_mut(&channel) {
                subscribers.retain(|&id| id != connection_id);
                if subscribers.is_empty() {
                    self.subscriptions.remove(&channel);
                }
            }

            // Remove from connection subscriptions
            if let Some(mut conn) = self.connections.get_mut(&connection_id) {
                conn.subscriptions.retain(|c| c != &channel);
            }
        }
    }

    /// Handle agent request
    async fn handle_agent_request(
        &self,
        _connection_id: Uuid,
        payload: AgentRequestPayload,
        sender: &mpsc::Sender<WebSocketMessage>,
    ) {
        // This would integrate with the orchestrator to execute agent tasks
        // For now, return a mock response
        
        let response = WebSocketMessage::AgentResponse(AgentResponsePayload {
            request_id: payload.request_id,
            success: true,
            response: Some(serde_json::json!({
                "message": "Agent request processed",
                "agent": payload.agent_name
            })),
            error: None,
            partial: false,
            final_response: true,
        });

        let _ = sender.send(response).await;
    }

    /// Handle broadcast message
    async fn handle_broadcast(&self, payload: BroadcastPayload) {
        if let Some(subscribers) = self.subscriptions.get(&payload.channel) {
            let message = WebSocketMessage::BroadcastMessage(payload);
            
            for &connection_id in subscribers.iter() {
                if let Some(sender) = self.connection_handlers.get(&connection_id) {
                    let _ = sender.send(message.clone()).await;
                }
            }
        }
    }

    /// Handle direct message
    async fn handle_direct_message(&self, payload: DirectMessagePayload) {
        // Find connection by user ID
        let recipient_connection = self.connections
            .iter()
            .find(|entry| {
                entry.value().user_id.as_ref() == Some(&payload.recipient_id)
            })
            .map(|entry| *entry.key());

        if let Some(connection_id) = recipient_connection {
            if let Some(sender) = self.connection_handlers.get(&connection_id) {
                let message = WebSocketMessage::DirectMessage(payload);
                let _ = sender.send(message).await;
            }
        }
    }

    /// Handle ping
    async fn handle_ping(&self, payload: PingPayload, sender: &mpsc::Sender<WebSocketMessage>) {
        let now = SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        let latency = now.saturating_sub(payload.timestamp);

        let pong = WebSocketMessage::Pong(PongPayload {
            timestamp: now,
            sequence: payload.sequence,
            latency_ms: latency,
        });

        let _ = sender.send(pong).await;
    }

    /// Broadcast message to channel
    pub async fn broadcast_to_channel(&self, channel: &str, message: WebSocketMessage) {
        if let Some(subscribers) = self.subscriptions.get(channel) {
            for &connection_id in subscribers.iter() {
                if let Some(sender) = self.connection_handlers.get(&connection_id) {
                    let _ = sender.send(message.clone()).await;
                }
            }
        }
    }

    /// Send message to specific connection
    pub async fn send_to_connection(&self, connection_id: Uuid, message: WebSocketMessage) -> Result<()> {
        if let Some(sender) = self.connection_handlers.get(&connection_id) {
            sender.send(message).await
                .map_err(|e| anyhow!("Failed to send message to connection {}: {}", connection_id, e))?;
        }
        Ok(())
    }

    /// Get WebSocket statistics
    pub async fn get_stats(&self) -> WebSocketStats {
        let mut stats = self.stats.read().await.clone();
        stats.active_connections = self.connections.len();
        stats.subscription_count = self.subscriptions.len();
        stats
    }

    /// Get active connections
    pub async fn get_connections(&self) -> Vec<WebSocketConnection> {
        self.connections.iter().map(|entry| entry.value().clone()).collect()
    }

    /// Cleanup connection
    async fn cleanup_connection(&self, connection_id: Uuid) {
        // Remove from connections
        if let Some((_, connection)) = self.connections.remove(&connection_id) {
            // Remove from all subscriptions
            for channel in &connection.subscriptions {
                if let Some(mut subscribers) = self.subscriptions.get_mut(channel) {
                    subscribers.retain(|&id| id != connection_id);
                    if subscribers.is_empty() {
                        self.subscriptions.remove(channel);
                    }
                }
            }
        }

        // Remove connection handler
        self.connection_handlers.remove(&connection_id);

        // Update stats
        let mut stats = self.stats.write().await;
        stats.active_connections = self.connections.len();

        info!("Cleaned up WebSocket connection: {}", connection_id);
    }

    /// Start ping task
    async fn start_ping_task(&self) {
        let connection_handlers = self.connection_handlers.clone();
        let interval = self.config.ping_interval_seconds;

        tokio::spawn(async move {
            let mut ping_interval = tokio::time::interval(Duration::from_secs(interval));
            let mut sequence = 0u64;

            loop {
                ping_interval.tick().await;
                sequence += 1;

                let ping_message = WebSocketMessage::Ping(PingPayload {
                    timestamp: SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap()
                        .as_millis() as u64,
                    sequence,
                });

                // Send ping to all connections
                for entry in connection_handlers.iter() {
                    let _ = entry.value().send(ping_message.clone()).await;
                }
            }
        });
    }

    /// Start cleanup task for inactive connections
    async fn start_cleanup_task(&self) {
        let connections = self.connections.clone();
        let connection_handlers = self.connection_handlers.clone();
        let timeout_duration = Duration::from_secs(self.config.connection_timeout_seconds);

        tokio::spawn(async move {
            let mut cleanup_interval = tokio::time::interval(Duration::from_secs(60)); // Check every minute

            loop {
                cleanup_interval.tick().await;
                let now = SystemTime::now();

                let inactive_connections: Vec<Uuid> = connections
                    .iter()
                    .filter_map(|entry| {
                        let connection = entry.value();
                        if now.duration_since(connection.last_activity).unwrap_or_default() > timeout_duration {
                            Some(connection.connection_id)
                        } else {
                            None
                        }
                    })
                    .collect();

                for connection_id in inactive_connections {
                    connections.remove(&connection_id);
                    connection_handlers.remove(&connection_id);
                    info!("Removed inactive WebSocket connection: {}", connection_id);
                }
            }
        });
    }

    /// Start statistics collection task
    async fn start_stats_task(&self) {
        let stats = self.stats.clone();
        let connections = self.connections.clone();

        tokio::spawn(async move {
            let mut stats_interval = tokio::time::interval(Duration::from_secs(30));

            loop {
                stats_interval.tick().await;

                let mut stats = stats.write().await;
                stats.active_connections = connections.len();
                
                // Calculate average latency and other metrics
                // This would be implemented with actual latency tracking
                stats.average_latency_ms = 25.0; // Mock value
            }
        });
    }
}
