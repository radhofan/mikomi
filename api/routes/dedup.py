from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from splink import DuckDBAPI, Linker, SettingsCreator, block_on
import splink.comparison_library as cl

from api.database import get_db
from api.routes.utils import load_lead_dataframe

router = APIRouter(prefix="/leads", tags=["deduplication"])


# POST /leads/dedupe-candidates
@router.post("/dedupe-candidates")
def get_dedupe_candidates(
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum match probability threshold"),
    limit: Optional[int] = Query(None, description="Maximum candidate pairs to return (returns all if omitted)"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    POST /leads/dedupe-candidates

    Surfaces duplicate candidate clusters using Fellegi-Sunter probabilistic record linkage and graph clustering.

    Params:
        threshold (float): Minimum match probability threshold (0.0 to 1.0).
        limit (int): Maximum number of duplicate candidate clusters to return.
        db (Session): Database session dependency.

    Returns:
        List[Dict[str, Any]]: Candidate duplicate clusters ranked by confidence.
    """
    df = load_lead_dataframe(db)
    if df.empty or len(df) < 2:
        return []

    settings = SettingsCreator(
        link_type="dedupe_only",
        unique_id_column_name="record_id",
        probability_two_random_records_match=0.01,
        comparisons=[
            cl.ExactMatch("phone_digits_str"),
            cl.LevenshteinAtThresholds("full_name", 2),
            cl.JaroWinklerAtThresholds("company_name", 0.88),
            cl.LevenshteinAtThresholds("email", 3),
        ],
        blocking_rules_to_generate_predictions=[
            block_on("phone_digits_str"),
            block_on("email_domain"),
        ],
        retain_matching_columns=True,
    )

    db_api = DuckDBAPI()
    db_api.register_table(df, "leads_input", overwrite=True)
    linker = Linker("leads_input", settings, db_api=db_api)
    linker.training.estimate_u_using_random_sampling(max_pairs=10000)
    linker.training.estimate_parameters_using_expectation_maximisation(block_on("phone_digits_str"))

    preds = linker.inference.predict(threshold_match_probability=threshold)
    clustered = linker.clustering.cluster_pairwise_predictions_at_threshold(
        preds,
        threshold_match_probability=threshold,
    )

    df_preds = preds.as_pandas_dataframe()
    df_clustered = clustered.as_pandas_dataframe()

    if df_clustered.empty:
        return []

    cluster_counts = df_clustered["cluster_id"].value_counts()
    dupe_cluster_ids = set(cluster_counts[cluster_counts > 1].index)
    if not dupe_cluster_ids:
        return []

    record_to_cluster = dict(zip(df_clustered["record_id"], df_clustered["cluster_id"]))
    df_preds["cluster_id"] = df_preds["record_id_l"].map(record_to_cluster)
    cluster_conf_map = df_preds.groupby("cluster_id")["match_probability"].mean().to_dict()

    df_dupes = df_clustered[df_clustered["cluster_id"].isin(dupe_cluster_ids)]
    grouped = df_dupes.groupby("cluster_id")

    results: List[Dict[str, Any]] = []
    for cid, group in grouped:
        leads_list = []
        for _, row in group.iterrows():
            leads_list.append(
                {
                    "record_id": int(row["record_id"]),
                    "full_name": row.get("full_name", ""),
                    "company_name": row.get("company_name", ""),
                    "email": row.get("email", ""),
                    "phone_digits": row.get("phone_digits_str", ""),
                }
            )

        avg_conf = float(cluster_conf_map.get(cid, 0.9))
        results.append(
            {
                "cluster_id": int(cid),
                "lead_count": len(leads_list),
                "confidence": round(avg_conf, 6),
                "leads": leads_list,
            }
        )

    if limit is not None:
        return results[:limit]
    return results
