import os

import pytest

from virtool_workflow.fixtures.scope import WorkflowFixtureScope

import workflow


@pytest.mark.asyncio
async def test_mk_index_dir(tmpdir):
    """
    Test that index dir is created successfully.
    """
    with WorkflowFixtureScope() as scope:
        scope["job_params"] = {"temp_index_path": f"{tmpdir}/foo"}
        bound_function = await scope.bind(workflow.mk_index_dir)
        await bound_function()

        assert os.path.exists(scope["job_params"]["temp_index_path"])
