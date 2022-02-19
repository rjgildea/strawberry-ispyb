import pytest

from ispyb_graphql.api import schema


@pytest.mark.asyncio
async def test_visit(mock_authentication, testdb):
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


@pytest.mark.asyncio
async def test_proposal(mock_authentication, testdb):
    query = """
query ProposalQuery {
  proposal(name: "cm14451") {
    name
    proposalId

    grid_scans: dataCollections(scanType: GRID) {
      dcid
    }

    samples {
      name
      sampleId
      crystalId

      dataCollections(scanType: ROTATION) {
        dcid
      }
    }
  }
}
    """

    result = await schema.schema.execute(
        query,
    )

    assert result.errors is None
    assert result.data == {
        "proposal": {
            "name": "cm14451",
            "proposalId": 37027,
            "grid_scans": [{"dcid": 6017405}],
            "samples": [
                {
                    "name": "thau8",
                    "sampleId": 398810,
                    "crystalId": 333301,
                    "dataCollections": [],
                },
                {
                    "name": "tlys_jan_4",
                    "sampleId": 374695,
                    "crystalId": 310037,
                    "dataCollections": [{"dcid": 993677}],
                },
                {
                    "name": "thau88",
                    "sampleId": 398816,
                    "crystalId": 310037,
                    "dataCollections": [],
                },
                {
                    "name": "thau99",
                    "sampleId": 398819,
                    "crystalId": 310037,
                    "dataCollections": [],
                },
                {
                    "name": "XPDF-1",
                    "sampleId": 398824,
                    "crystalId": 333308,
                    "dataCollections": [],
                },
                {
                    "name": "XPDF-2",
                    "sampleId": 398827,
                    "crystalId": 333308,
                    "dataCollections": [],
                },
            ],
        }
    }


@pytest.mark.asyncio
async def test_beamline(mock_authentication, testdb):
    query = """
query BeamlineQuery {
  beamline(name: "i03") {
    name

    visits {
      name
    }

    dataCollections {
      dcid
    }
  }
}
    """

    result = await schema.schema.execute(
        query,
    )

    assert result.errors is None
    assert result.data == {
        "beamline": {
            "name": "i03",
            "visits": [{"name": "cm14451-1"}, {"name": "cm14451-2"}],
            "dataCollections": [
                {"dcid": 993677},
                {"dcid": 1002287},
                {"dcid": 6017405},
                {"dcid": 1052494},
                {"dcid": 1052503},
                {"dcid": 1066786},
            ],
        }
    }
