#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Grouping Phase (Entry Point)
"""

import sys
import json
from group_jobs import process_grouping
from phase_utils import get_common_parser, load_phase_json

def main():
    """Main execution function for Phase 3: Grouping."""
    parser = get_common_parser("Phase 3: Grouping Phase")
    args = parser.parse_args()

    p2_data = load_phase_json(args.in_json)

    dispatch_text = p2_data.get("content", p2_data.get("dispatch_out", ""))
    translated_text = p2_data.get("translated_text", "")
    if not dispatch_text:
        sys.exit(1)

    print(f"Grouping Phase starting for: {args.uuid}\n")

    result = process_grouping(dispatch_text, args.host, args.port, args.model, translated_text)

    # Save the result
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
