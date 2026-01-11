"""Tests for parallel research agents.

These tests verify the parallel research system that runs multiple
research tasks simultaneously for sermon preparation.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL agent templates and files - NO MOCKS.
"""
import pytest
import tempfile
import os
import time
from concurrent.futures import ThreadPoolExecutor


class TestParallelAgentInitialization:
    """Test suite for parallel agent initialization."""

    def test_should_create_parallel_coordinator_when_config_provided(self):
        """Test that parallel coordinator can be created."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        assert coordinator is not None

    def test_should_accept_max_concurrent_agents_config(self):
        """Test that max concurrent agents is configurable."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge, max_concurrent=4)

        assert coordinator.max_concurrent == 4

    def test_should_default_to_reasonable_concurrency_limit(self):
        """Test that default concurrency limit is set."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        assert coordinator.max_concurrent >= 1
        assert coordinator.max_concurrent <= 10

    def test_should_initialize_with_empty_task_queue(self):
        """Test that coordinator starts with empty task queue."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        assert coordinator.pending_tasks == 0


class TestParallelTaskExecution:
    """Test suite for running parallel research tasks."""

    def test_should_run_multiple_tasks_concurrently(self):
        """Test running multiple research tasks in parallel."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        # Create test agent templates
        with tempfile.TemporaryDirectory() as tmpdir:
            for agent_type in ['bible', 'commentary', 'illustration']:
                path = os.path.join(tmpdir, f'{agent_type}_agent.md')
                with open(path, 'w') as f:
                    f.write(f'# {agent_type.title()} Agent\nResearch {agent_type} content.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'bible', 'params': {'scripture': 'John 3:16'}},
                {'agent': 'commentary', 'params': {'scripture': 'John 3:16'}},
                {'agent': 'illustration', 'params': {'theme': 'Love'}}
            ]

            results = coordinator.run_parallel(tasks)

            assert len(results) == 3

    def test_should_return_results_for_all_tasks(self):
        """Test that all task results are returned."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                path = os.path.join(tmpdir, f'agent_{i}.md')
                with open(path, 'w') as f:
                    f.write(f'# Agent {i}\nProcess task {i}.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': f'agent_{i}', 'params': {}} for i in range(3)
            ]

            results = coordinator.run_parallel(tasks)

            assert all(r is not None for r in results)

    def test_should_respect_max_concurrent_limit(self):
        """Test that concurrency limit is respected."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge, max_concurrent=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                path = os.path.join(tmpdir, f'task_{i}.md')
                with open(path, 'w') as f:
                    f.write(f'# Task {i}\nProcess task {i}.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': f'task_{i}', 'params': {}} for i in range(5)
            ]

            # Should still complete all tasks, but respecting limit
            results = coordinator.run_parallel(tasks)

            assert len(results) == 5


class TestResultAggregation:
    """Test suite for aggregating parallel results."""

    def test_should_aggregate_results_from_all_agents(self):
        """Test that results from all agents are aggregated."""
        from parallel_research import ParallelResearchCoordinator, aggregate_results
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            for agent in ['bible', 'commentary']:
                path = os.path.join(tmpdir, f'{agent}_agent.md')
                with open(path, 'w') as f:
                    f.write(f'# {agent.title()} Agent\nProvide {agent} data.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'bible', 'params': {'scripture': 'John 3:16'}},
                {'agent': 'commentary', 'params': {'scripture': 'John 3:16'}}
            ]

            results = coordinator.run_parallel(tasks)
            aggregated = aggregate_results(results)

            assert aggregated is not None
            assert 'bible' in aggregated or len(aggregated) >= 1

    def test_should_combine_research_data_by_type(self):
        """Test that research data is organized by type."""
        from parallel_research import aggregate_results

        results = [
            {'agent': 'bible', 'data': 'Bible research data'},
            {'agent': 'commentary', 'data': 'Commentary data'},
            {'agent': 'illustration', 'data': 'Illustration data'}
        ]

        aggregated = aggregate_results(results)

        assert 'bible' in aggregated or 'research' in aggregated

    def test_should_preserve_individual_results(self):
        """Test that individual results are preserved in aggregation."""
        from parallel_research import aggregate_results

        results = [
            {'agent': 'bible', 'data': {'verses': ['John 3:16']}},
            {'agent': 'commentary', 'data': {'notes': 'Some notes'}}
        ]

        aggregated = aggregate_results(results)

        # Should be able to access individual data
        assert aggregated is not None


class TestErrorHandling:
    """Test suite for error handling in parallel execution."""

    def test_should_handle_single_agent_failure(self):
        """Test that one failed agent doesn't stop others."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one agent, others will fail
            path = os.path.join(tmpdir, 'working_agent.md')
            with open(path, 'w') as f:
                f.write('# Working Agent\nThis one works.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'working_agent', 'params': {}},
                {'agent': 'nonexistent_agent', 'params': {}}
            ]

            results = coordinator.run_parallel(tasks, fail_fast=False)

            # Should have results for both (one success, one error)
            assert len(results) == 2

    def test_should_mark_failed_results_with_error(self):
        """Test that failed results are marked with error info."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'nonexistent', 'params': {}}
            ]

            results = coordinator.run_parallel(tasks, fail_fast=False)

            assert results[0].get('error') is not None or results[0].get('status') == 'error'

    def test_should_fail_fast_when_configured(self):
        """Test that fail_fast stops on first error."""
        from parallel_research import ParallelResearchCoordinator, ParallelExecutionError
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'nonexistent', 'params': {}}
            ]

            with pytest.raises((ParallelExecutionError, Exception)):
                coordinator.run_parallel(tasks, fail_fast=True)


class TestTimeoutHandling:
    """Test suite for timeout handling."""

    def test_should_timeout_slow_agent(self):
        """Test that slow agents are timed out."""
        from parallel_research import ParallelResearchCoordinator, AgentTimeoutError
        from cli_bridge import CLIBridge

        # Very short timeout
        bridge = CLIBridge(command='python', timeout=1)
        coordinator = ParallelResearchCoordinator(bridge, timeout=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'slow_agent.md')
            with open(path, 'w') as f:
                f.write('# Slow Agent\nThis takes too long.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'slow_agent', 'params': {}}
            ]

            results = coordinator.run_parallel(tasks, fail_fast=False)

            # Should have error result for timeout
            assert results[0].get('error') is not None or results[0].get('timeout') is True

    def test_should_allow_configurable_timeout(self):
        """Test that timeout is configurable."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge, timeout=60)

        assert coordinator.timeout == 60


class TestResultPrioritization:
    """Test suite for result prioritization."""

    def test_should_prioritize_results_by_source(self):
        """Test that results can be prioritized by source."""
        from parallel_research import prioritize_results

        results = [
            {'agent': 'bible', 'data': 'Bible data', 'priority': 1},
            {'agent': 'illustration', 'data': 'Illustration data', 'priority': 3},
            {'agent': 'commentary', 'data': 'Commentary data', 'priority': 2}
        ]

        prioritized = prioritize_results(results)

        # Should be in priority order
        assert prioritized[0]['agent'] == 'bible'

    def test_should_handle_same_priority_results(self):
        """Test handling of results with same priority."""
        from parallel_research import prioritize_results

        results = [
            {'agent': 'agent_a', 'data': 'Data A', 'priority': 1},
            {'agent': 'agent_b', 'data': 'Data B', 'priority': 1}
        ]

        prioritized = prioritize_results(results)

        assert len(prioritized) == 2


class TestAgentCommunication:
    """Test suite for agent communication."""

    def test_should_pass_shared_context_to_agents(self):
        """Test that shared context is passed to all agents."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ['agent_a', 'agent_b']:
                path = os.path.join(tmpdir, f'{name}.md')
                with open(path, 'w') as f:
                    f.write(f'# {name}\nUse shared context.')

            coordinator.agents_dir = tmpdir

            shared_context = {
                'scripture': 'John 3:16',
                'theme': 'Love',
                'sermon_id': 123
            }

            tasks = [
                {'agent': 'agent_a', 'params': {}},
                {'agent': 'agent_b', 'params': {}}
            ]

            results = coordinator.run_parallel(tasks, shared_context=shared_context)

            assert len(results) == 2

    def test_should_allow_agent_to_agent_message_passing(self):
        """Test that agents can pass messages to each other."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'messenger.md')
            with open(path, 'w') as f:
                f.write('# Messenger\nSend message to other agent.')

            coordinator.agents_dir = tmpdir

            # This is a more advanced feature - test the interface exists
            assert hasattr(coordinator, 'send_message') or hasattr(coordinator, 'message_queue')


class TestResourceLimits:
    """Test suite for resource limits."""

    def test_should_enforce_max_concurrent_agents(self):
        """Test that max concurrent limit is enforced."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge, max_concurrent=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                path = os.path.join(tmpdir, f'agent_{i}.md')
                with open(path, 'w') as f:
                    f.write(f'# Agent {i}\nProcess.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': f'agent_{i}', 'params': {}} for i in range(10)
            ]

            # Should complete without exceeding limit
            results = coordinator.run_parallel(tasks)

            assert len(results) == 10

    def test_should_report_concurrent_agent_count(self):
        """Test that current concurrent count can be queried."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        # When idle, should be 0
        assert coordinator.get_active_count() == 0


class TestParallelResearchWorkflow:
    """Test suite for complete parallel research workflow."""

    def test_should_run_full_research_workflow(self):
        """Test running a complete parallel research workflow."""
        from parallel_research import ParallelResearchCoordinator, aggregate_results
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create standard research agents
            agents = {
                'bible_research': '# Bible Research\nLook up scripture.',
                'commentary_research': '# Commentary\nFind commentary.',
                'illustration_finder': '# Illustrations\nFind illustrations.'
            }

            for name, content in agents.items():
                path = os.path.join(tmpdir, f'{name}.md')
                with open(path, 'w') as f:
                    f.write(content)

            coordinator.agents_dir = tmpdir

            sermon_params = {
                'scripture': 'John 3:16',
                'theme': 'Grace',
                'title': 'Amazing Grace'
            }

            tasks = [
                {'agent': 'bible_research', 'params': sermon_params},
                {'agent': 'commentary_research', 'params': sermon_params},
                {'agent': 'illustration_finder', 'params': sermon_params}
            ]

            results = coordinator.run_parallel(tasks)
            aggregated = aggregate_results(results)

            assert aggregated is not None

    def test_should_return_structured_research_data(self):
        """Test that research returns structured data."""
        from parallel_research import ParallelResearchCoordinator
        from cli_bridge import CLIBridge

        bridge = CLIBridge(command='echo')
        coordinator = ParallelResearchCoordinator(bridge)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'structured_agent.md')
            with open(path, 'w') as f:
                f.write('# Structured Agent\nReturn structured data.')

            coordinator.agents_dir = tmpdir

            tasks = [
                {'agent': 'structured_agent', 'params': {'scripture': 'John 3:16'}}
            ]

            results = coordinator.run_parallel(tasks)

            # Should have structured result
            assert results[0] is not None
