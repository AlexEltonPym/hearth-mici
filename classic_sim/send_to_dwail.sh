local_directory="/home/alex"
hosts=("dwail1" "dwail2")
for host in ${hosts[*]};
  do
    target=${host}:${local_directory}
    echo "Transfering to ${target}" 
    rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' --exclude '.pyenv' --exclude '.venv' ../classic_sim ${target}
  done

  # rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim ${host}:{$local_directory}





# rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim dwail2:/home/alex
# rsync -vzr --progress --exclude '*.pickle' --exclude 'dwailmeta' --exclude 'examples/archive' --exclude 'examples/experiment_results'  --exclude 'examples/metaspace_generation/data' --exclude 'examples/metaspace_generation/data_archive'  --include 'examples/metagame_analysis/metagame' --exclude 'venv' ../classic_sim dwail1:/home/alex
