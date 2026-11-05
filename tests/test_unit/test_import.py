def test_import_pipeline():
    """The public Pipeline class can be imported."""
    from spikesorted import Pipeline

    assert Pipeline.__name__ == "Pipeline"
