local_directory="/home/alex"
hosts=("dwail1" "dwail2")
# for host in ${hosts[*]};
  # do
  #   target=${host}:${local_directory}
  #   echo "Transfering to ${target}" 
  #   rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta_0' --exclude 'dwailmeta_1' --exclude 'dwailmeta_2' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' --exclude '.pyenv' --exclude '.venv' ../classic_sim ${target}
  # done

  # rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim ${host}:{$local_directory}


  # Define excludes in an array for neatness
excludes=(
  '*.pickle'
  'dwailmeta_*'
  'examples/archive'
  'examples/experiment_results'
  'examples/metaspace_generation/data'
  'examples/metaspace_generation/data_archive'
  'venv'
  '.pyenv'
  '.venv'
)

# Build rsync exclude arguments
exclude_args=()
for ex in "${excludes[@]}"; do
  exclude_args+=(--exclude "$ex")
done

# Add include argument
include_args=(--include 'examples/metagame_analysis/metagame')

# Rsync using neat exclude/include arrays
for host in "${hosts[@]}"; do
  target="${host}:${local_directory}"
  echo "Neat transfer to ${target}"
  rsync -vzr --progress "${exclude_args[@]}" "${include_args[@]}" ../classic_sim "${target}"
done


# rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim dwail2:/home/alex
# rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim dwail1:/home/alex
