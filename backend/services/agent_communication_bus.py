"""
Agent Communication Bus for inter-agent messaging and collaboration
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import defaultdict

from models.agent import AgentMessage, MessageType

logger = logging.getLogger(__name__)

class AgentCommunicationBus:
    """
    Communication bus for managing inter-agent messaging and collaboration.
    Handles message routing, delivery, and coordination between agents.
    """
    
    def __init__(self, max_message_history: int = 1000):
        """
        Initialize the communication bus
        
        Args:
            max_message_history: Maximum number of messages to keep in history
        """
        self.max_message_history = max_message_history
        
        # Agent registry
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        
        # Message handling
        self.message_history: List[AgentMessage] = []
        self.message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.message_handlers: Dict[str, Dict[MessageType, Callable]] = defaultdict(dict)
        
        # Broadcast subscribers
        self.broadcast_subscribers: Dict[MessageType, List[str]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            "total_messages": 0,
            "messages_by_type": defaultdict(int),
            "messages_by_agent": defaultdict(int),
            "failed_deliveries": 0,
            "broadcast_count": 0
        }
        
        # Background tasks
        self._running = False
        self._message_processor_task = None
        
        logger.info("Agent Communication Bus initialized")
    
    async def start(self):
        """Start the communication bus background processing"""
        if self._running:
            return
        
        self._running = True
        self._message_processor_task = asyncio.create_task(self._process_messages())
        logger.info("Agent Communication Bus started")
    
    async def stop(self):
        """Stop the communication bus"""
        self._running = False
        
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Agent Communication Bus stopped")
    
    def register_agent(self, agent_id: str, agent_instance: Any):
        """
        Register an agent with the communication bus
        
        Args:
            agent_id: Unique identifier for the agent
            agent_instance: The agent instance
        """
        self.agents[agent_id] = agent_instance
        
        # Set the communication bus reference in the agent
        if hasattr(agent_instance, 'set_communication_bus'):
            agent_instance.set_communication_bus(self)
        
        logger.info(f"Registered agent {agent_id} with communication bus")
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the communication bus
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
        
        # Clean up message queue
        if agent_id in self.message_queues:
            del self.message_queues[agent_id]
        
        # Remove from broadcast subscribers
        for message_type in self.broadcast_subscribers:
            if agent_id in self.broadcast_subscribers[message_type]:
                self.broadcast_subscribers[message_type].remove(agent_id)
        
        logger.info(f"Unregistered agent {agent_id} from communication bus")
    
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message to a specific agent
        
        Args:
            message: The message to send
            
        Returns:
            True if message was queued successfully
        """
        try:
            # Validate recipient exists
            if message.recipient_agent_id not in self.agents:
                logger.warning(f"Recipient agent {message.recipient_agent_id} not found")
                self.stats["failed_deliveries"] += 1
                return False
            
            # Add to message queue
            await self.message_queues[message.recipient_agent_id].put(message)
            
            # Update statistics
            self.stats["total_messages"] += 1
            self.stats["messages_by_type"][message.message_type] += 1
            self.stats["messages_by_agent"][message.sender_agent_id] += 1
            
            # Add to history
            self._add_to_history(message)
            
            logger.debug(f"Queued message from {message.sender_agent_id} to {message.recipient_agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            self.stats["failed_deliveries"] += 1
            return False
    
    async def broadcast_message(self, sender_id: str, message_type: MessageType, content: Dict[str, Any]) -> bool:
        """
        Broadcast a message to all subscribed agents
        
        Args:
            sender_id: ID of the sending agent
            message_type: Type of message to broadcast
            content: Message content
            
        Returns:
            True if broadcast was successful
        """
        try:
            subscribers = self.broadcast_subscribers.get(message_type, [])
            
            if not subscribers:
                logger.info(f"No subscribers for broadcast message type {message_type}")
                return True
            
            # Send to all subscribers
            success_count = 0
            for recipient_id in subscribers:
                if recipient_id != sender_id:  # Don't send to self
                    message = AgentMessage(
                        sender_agent_id=sender_id,
                        recipient_agent_id=recipient_id,
                        message_type=message_type,
                        content=content
                    )
                    
                    if await self.send_message(message):
                        success_count += 1
            
            self.stats["broadcast_count"] += 1
            logger.info(f"Broadcast message from {sender_id} to {success_count} agents")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {str(e)}")
            return False
    
    def subscribe_to_broadcasts(self, agent_id: str, message_types: List[MessageType]):
        """
        Subscribe an agent to broadcast messages of specific types
        
        Args:
            agent_id: ID of the agent to subscribe
            message_types: List of message types to subscribe to
        """
        for message_type in message_types:
            if agent_id not in self.broadcast_subscribers[message_type]:
                self.broadcast_subscribers[message_type].append(agent_id)
        
        logger.info(f"Agent {agent_id} subscribed to broadcasts: {[mt.value for mt in message_types]}")
    
    def unsubscribe_from_broadcasts(self, agent_id: str, message_types: List[MessageType]):
        """
        Unsubscribe an agent from broadcast messages
        
        Args:
            agent_id: ID of the agent to unsubscribe
            message_types: List of message types to unsubscribe from
        """
        for message_type in message_types:
            if agent_id in self.broadcast_subscribers[message_type]:
                self.broadcast_subscribers[message_type].remove(agent_id)
        
        logger.info(f"Agent {agent_id} unsubscribed from broadcasts: {[mt.value for mt in message_types]}")
    
    async def _process_messages(self):
        """Background task to process and deliver messages"""
        while self._running:
            try:
                # Process messages for each agent
                for agent_id, queue in self.message_queues.items():
                    if not queue.empty():
                        try:
                            # Get message from queue (non-blocking)
                            message = queue.get_nowait()
                            
                            # Deliver to agent
                            await self._deliver_message(agent_id, message)
                            
                        except asyncio.QueueEmpty:
                            continue
                        except Exception as e:
                            logger.error(f"Error processing message for agent {agent_id}: {str(e)}")
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in message processor: {str(e)}")
                await asyncio.sleep(1)  # Longer delay on error
    
    async def _deliver_message(self, agent_id: str, message: AgentMessage):
        """
        Deliver a message to a specific agent
        
        Args:
            agent_id: ID of the recipient agent
            message: Message to deliver
        """
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                logger.warning(f"Agent {agent_id} not found for message delivery")
                self.stats["failed_deliveries"] += 1
                return
            
            # Deliver message to agent
            if hasattr(agent, 'receive_message'):
                success = await agent.receive_message(message)
                if success:
                    message.acknowledged = True
                    logger.debug(f"Message delivered to agent {agent_id}")
                else:
                    logger.warning(f"Agent {agent_id} failed to handle message")
                    self.stats["failed_deliveries"] += 1
            else:
                logger.warning(f"Agent {agent_id} does not support message receiving")
                self.stats["failed_deliveries"] += 1
                
        except Exception as e:
            logger.error(f"Failed to deliver message to agent {agent_id}: {str(e)}")
            self.stats["failed_deliveries"] += 1
    
    def _add_to_history(self, message: AgentMessage):
        """Add message to history with size limit"""
        self.message_history.append(message)
        
        # Trim history if it exceeds max size
        if len(self.message_history) > self.max_message_history:
            self.message_history = self.message_history[-self.max_message_history:]
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: Optional[int] = None
    ) -> List[AgentMessage]:
        """
        Get message history with optional filtering
        
        Args:
            agent_id: Filter by sender or recipient agent ID
            message_type: Filter by message type
            limit: Maximum number of messages to return
            
        Returns:
            List of messages matching the criteria
        """
        messages = self.message_history
        
        # Apply filters
        if agent_id:
            messages = [
                msg for msg in messages
                if msg.sender_agent_id == agent_id or msg.recipient_agent_id == agent_id
            ]
        
        if message_type:
            messages = [msg for msg in messages if msg.message_type == message_type]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get communication bus statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_messages": self.stats["total_messages"],
            "messages_by_type": dict(self.stats["messages_by_type"]),
            "messages_by_agent": dict(self.stats["messages_by_agent"]),
            "failed_deliveries": self.stats["failed_deliveries"],
            "broadcast_count": self.stats["broadcast_count"],
            "registered_agents": len(self.agents),
            "active_queues": len([q for q in self.message_queues.values() if not q.empty()]),
            "broadcast_subscribers": {
                mt.value: len(subscribers) 
                for mt, subscribers in self.broadcast_subscribers.items()
            },
            "message_history_size": len(self.message_history)
        }
    
    def clear_statistics(self):
        """Clear all statistics"""
        self.stats = {
            "total_messages": 0,
            "messages_by_type": defaultdict(int),
            "messages_by_agent": defaultdict(int),
            "failed_deliveries": 0,
            "broadcast_count": 0
        }
        logger.info("Communication bus statistics cleared")
    
    def get_agent_list(self) -> List[str]:
        """Get list of registered agent IDs"""
        return list(self.agents.keys())
    
    async def ping_agent(self, agent_id: str) -> bool:
        """
        Ping an agent to check if it's responsive
        
        Args:
            agent_id: ID of the agent to ping
            
        Returns:
            True if agent is responsive
        """
        if agent_id not in self.agents:
            return False
        
        try:
            # Send a ping message
            ping_message = AgentMessage(
                sender_agent_id="communication_bus",
                recipient_agent_id=agent_id,
                message_type=MessageType.STATUS_UPDATE,
                content={"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            )
            
            return await self.send_message(ping_message)
            
        except Exception as e:
            logger.error(f"Failed to ping agent {agent_id}: {str(e)}")
            return False