import pytest

from ispyb_graphql.api import schema


@pytest.mark.asyncio
async def test_visit(mocker, testdb):

    query = """
query VisitQuery {
  visit(name: "cm14451-1") {
    name
    sessionId

    grid_scans: dataCollections(scanType: GRID) {
      dcid
    }

    rotation_scans: dataCollections(scanType: ROTATION) {
      dcid
    }
  }
}
    """

    mocker.patch.object(schema.IsAuthenticated, "has_permission")
    result = await schema.schema.execute(
        query,
    )

    assert result.errors is None
    assert result.data == {
        "visit": {
            "name": "cm14451-1",
            "sessionId": 55167,
            "grid_scans": [{"dcid": 6017405}],
            "rotation_scans": [{"dcid": 993677}, {"dcid": 1002287}],
        }
    }
