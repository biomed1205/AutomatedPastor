"""Parallel research module for concurrent agent execution.

Provides parallel execution of multiple research agents for
faster sermon preparation.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from queue import Queue
from typing import List, Dict, Any, Optional


class ParallelExecutionError(Exception):
    """Raised when parallel execution fails and fail_fast is enabled."""
    pass


class AgentTimeoutError(Exception):
    """Raised when an agent exceeds the timeout limit."""
    pass


class ParallelResearchCoordinator:
    """Coordinator for running multiple research agents in parallel.

    Manages concurrent execution of research tasks with configurable
    concurrency limits, timeout handling, and error management.
    """

    def __init__(self, bridge, max_concurrent: int = 3, timeout: int = None):
        """Initialize the parallel research coordinator.

        Args:
            bridge: CLIBridge instance for running agents.
            max_concurrent: Maximum number of concurrent agents (1-10).
            timeout: Timeout in seconds for each agent.
        """
        self.bridge = bridge
        self.max_concurrent = min(max(1, max_concurrent), 10)
        self.timeout = timeout if timeout is not None else 300
        self.agents_dir = '.'
        self.pending_tasks = 0
        self._active_count = 0
        self._active_lock = threading.Lock()
        self.message_queue = Queue()

    def get_active_count(self) -> int:
        """Get the number of currently active agents.

        Returns:
            int: Number of active agents.
        """
        with self._active_lock:
            return self._active_count

    def _increment_active(self):
        """Increment the active agent count."""
        with self._active_lock:
            self._active_count += 1

    def _decrement_active(self):
        """Decrement the active agent count."""
        with self._active_lock:
            self._active_count -= 1

    def send_message(self, from_agent: str, to_agent: str, message: str):
        """Send a message from one agent to another.

        Args:
            from_agent: Name of the sending agent.
            to_agent: Name of the receiving agent.
            message: Message content.
        """
        self.message_queue.put({
            'from': from_agent,
            'to': to_agent,
            'message': message
        })

    def _load_agent_template(self, agent_name: str) -> Optional[str]:
        """Load an agent template from the agents directory.

        Args:
            agent_name: Name of the agent.

        Returns:
            str: Agent template content or None if not found.
        """
        # Try different naming patterns
        patterns = [
            f'{agent_name}.md',
            f'{agent_name}_agent.md',
            f'{agent_name}_research.md'
        ]

        for pattern in patterns:
            path = os.path.join(self.agents_dir, pattern)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()

        return None

    def _run_single_task(self, task: Dict[str, Any], shared_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run a single research task.

        Args:
            task: Task definition with 'agent' and 'params'.
            shared_context: Optional shared context for all agents.

        Returns:
            dict: Result with agent name, data, and status.
        """
        agent_name = task.get('agent', 'unknown')
        params = task.get('params', {})

        try:
            self._increment_active()

            # Load agent template
            template = self._load_agent_template(agent_name)
            if template is None:
                return {
                    'agent': agent_name,
                    'data': None,
                    'status': 'error',
                    'error': f'Agent template not found: {agent_name}'
                }

            # Build prompt with parameters and shared context
            prompt_parts = [template]

            if shared_context:
                prompt_parts.append(f"\nShared Context: {shared_context}")

            if params:
                prompt_parts.append(f"\nParameters: {params}")

            prompt = '\n'.join(str(p) for p in prompt_parts)

            # Run via CLI bridge
            result = self.bridge.run(prompt)

            output = result.output if hasattr(result, 'output') else str(result)

            # Check if the command failed
            if hasattr(result, 'success') and not result.success:
                return {
                    'agent': agent_name,
                    'data': None,
                    'status': 'error',
                    'error': result.stderr if hasattr(result, 'stderr') and result.stderr else 'Command failed',
                    'exit_code': result.exit_code if hasattr(result, 'exit_code') else 1
                }

            return {
                'agent': agent_name,
                'data': output,
                'status': 'success',
                'params': params
            }

        except Exception as e:
            # Check for timeout-related errors
            error_str = str(e).lower()
            is_timeout = isinstance(e, FuturesTimeoutError) or 'timeout' in error_str
            return {
                'agent': agent_name,
                'data': None,
                'status': 'error',
                'error': str(e) if str(e) else 'Agent timed out',
                'timeout': is_timeout or None
            }
        finally:
            self._decrement_active()

    def run_parallel(self, tasks: List[Dict[str, Any]],
                     fail_fast: bool = False,
                     shared_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Run multiple research tasks in parallel.

        Args:
            tasks: List of task definitions, each with 'agent' and 'params'.
            fail_fast: If True, raise exception on first error.
            shared_context: Optional shared context passed to all agents.

        Returns:
            list: List of results from all tasks.

        Raises:
            ParallelExecutionError: If fail_fast is True and any task fails.
        """
        results = []
        self.pending_tasks = len(tasks)

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._run_single_task, task, shared_context): task
                for task in tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                agent_name = task.get('agent', 'unknown')
                self.pending_tasks -= 1

                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)

                    if fail_fast and result.get('status') == 'error':
                        raise ParallelExecutionError(
                            f"Agent {agent_name} failed: {result.get('error')}"
                        )

                except ParallelExecutionError:
                    raise

                except Exception as e:
                    is_timeout = isinstance(e, FuturesTimeoutError) or 'timeout' in str(e).lower()
                    result = {
                        'agent': agent_name,
                        'data': None,
                        'status': 'error',
                        'error': str(e) if str(e) else 'Task error',
                        'timeout': is_timeout or None
                    }
                    results.append(result)

                    if fail_fast:
                        raise ParallelExecutionError(f"Agent {agent_name} failed: {e}")

        return results


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate results from multiple agents.

    Args:
        results: List of result dictionaries from agents.

    Returns:
        dict: Aggregated results organized by agent/type.
    """
    aggregated = {
        'research': {},
        'by_agent': {},
        'errors': []
    }

    for result in results:
        agent = result.get('agent', 'unknown')
        status = result.get('status', 'unknown')

        if status == 'error':
            aggregated['errors'].append({
                'agent': agent,
                'error': result.get('error')
            })
        else:
            aggregated['by_agent'][agent] = result.get('data')

            # Also organize by research type
            if 'bible' in agent.lower():
                aggregated['research']['bible'] = result.get('data')
                aggregated['bible'] = result.get('data')
            elif 'commentary' in agent.lower():
                aggregated['research']['commentary'] = result.get('data')
                aggregated['commentary'] = result.get('data')
            elif 'illustration' in agent.lower():
                aggregated['research']['illustration'] = result.get('data')
                aggregated['illustration'] = result.get('data')
            else:
                aggregated['research'][agent] = result.get('data')

    return aggregated


def prioritize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioritize results by source/priority.

    Args:
        results: List of result dictionaries.

    Returns:
        list: Results sorted by priority (lower priority number = higher priority).
    """
    def get_priority(result):
        # Use explicit priority if set, default to 10
        return result.get('priority', 10)

    return sorted(results, key=get_priority)
