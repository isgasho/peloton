import grpc
import time

import pytest

from tests.integration.aurorabridge_test.client import Client
from tests.integration.stateless_job import query_jobs


@pytest.fixture
def client():
    client = Client()

    yield client

    # Delete all jobs
    _delete_jobs()


def _delete_jobs(respool_path='/AuroraBridge',
                 timeout_secs=20):
    jobs = query_jobs(respool_path)

    for job in jobs:
        job.delete(force_delete=True)

    # Wait for job deletion to complete.
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        try:
            jobs = query_jobs(respool_path)
            if len(jobs) == 0:
                return
            time.sleep(2)
        except grpc.RpcError as e:
            # Catch "not-found" error here because QueryJobs endpoint does
            # two db queries in sequence: "QueryJobs" and "GetUpdate".
            # However, when we delete a job, updates are deleted first,
            # there is a slight chance QueryJobs will fail to query the
            # update, returning "not-found" error.
            if e.code() == grpc.StatusCode.NOT_FOUND:
                time.sleep(2)
                continue
            raise

    assert False, 'timed out waiting for jobs to be deleted'
