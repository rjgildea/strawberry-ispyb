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


@pytest.mark.asyncio
async def test_data_collection(mock_authentication, testdb):
    query = """
query DataCollectionQuery {
  dataCollection(dcid: 993677) {
    dcid
    filename
    startTime
    endTime
    axisStart
    axisEnd
    axisRange
    overlap
    numberOfImages
    startImageNumber
    exposureTime
    rotationAxis
    phiStart
    kappaStart
    omegaStart
    chiStart

    sample {
      name
    }

    autoProcessings {
      program
      spaceGroup
    }
  }
}
    """

    result = await schema.schema.execute(
        query,
    )

    assert result.errors is None
    assert result.data == {
        "dataCollection": {
            "dcid": 993677,
            "filename": "/dls/i03/data/2016/cm14451-1/20160114/tlys_jan_4/tlys_jan_4_1_####.cbf",
            "startTime": "2016-01-14T12:40:34",
            "endTime": "2016-01-14T12:41:54",
            "axisStart": 45.0,
            "axisEnd": 0.1,
            "axisRange": 0.1,
            "overlap": 0.0,
            "numberOfImages": 3600,
            "startImageNumber": 1,
            "exposureTime": 0.02,
            "rotationAxis": "Omega",
            "phiStart": None,
            "kappaStart": None,
            "omegaStart": 45.0,
            "chiStart": None,
            "sample": {"name": "tlys_jan_4"},
            "autoProcessings": [
                {"program": "fast_dp", "spaceGroup": "P 6 2 2"},
                {"program": "xia2 3dii", "spaceGroup": "P 63 2 2"},
                {"program": "xia2 dials", "spaceGroup": "P 61 2 2"},
                {
                    "program": "autoPROC 1.0.4 (see: http://www.globalphasing.com/autoproc/)",
                    "spaceGroup": "P 63 2 2",
                },
                {"program": "xia2 dials", "spaceGroup": "P 61 2 2"},
                {"program": "xia2 dials", "spaceGroup": "P 61 2 2"},
                {"program": "xia2 3dii", "spaceGroup": "P 63 2 2"},
                {"program": "xia2 3dii", "spaceGroup": "P 63 2 2"},
            ],
        }
    }


@pytest.mark.asyncio
async def test_sample(mock_authentication, testdb):
    query = """
query SampleQuery {
  sample(sampleId: 374695) {
    name

    dataCollections(scanType: ROTATION) {
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
        "sample": {"name": "tlys_jan_4", "dataCollections": [{"dcid": 993677}]}
    }
