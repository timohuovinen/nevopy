# MIT License
#
# Copyright (c) 2020 Gabriel Nogueira (Talendar)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

"""
TODO
"""

import numpy as np
from nevopy.neat.genome import Genome, mate_genomes
from nevopy.neat.genes import NodeGene
from nevopy.neat.config import Config
from nevopy.neat.id_handler import IdHandler
from nevopy.neat.species import Species
from nevopy import utils
from nevopy.processing.pool_processing import PoolProcessingScheduler
from typing import Optional, Callable


class Population:
    """
    TODO
    """

    def __init__(self,
                 size,
                 num_inputs,
                 num_outputs,
                 config=None,
                 processing_scheduler=None) -> None:
        self._size = size
        self._num_inputs = num_inputs
        self._num_outputs = num_outputs

        self._scheduler = (PoolProcessingScheduler
                           if processing_scheduler is not None
                           else PoolProcessingScheduler())

        self.config = config if config is not None else Config()
        self._id_handler = IdHandler(num_inputs, num_outputs,
                                     has_bias=self.config.bias_value is not None)
        self._rank_prob_dist = None
        self._invalid_genomes_replaced = None

        self.__mmh_nodes = None
        self.__mmh_connections = None

        # creating initial genomes
        self.genomes = [Genome(genome_id=self._id_handler.next_genome_id(),
                               num_inputs=num_inputs,
                               num_outputs=num_outputs,
                               config=self.config)
                        for _ in range(size)]

        # creating pioneer species
        new_sp = Species(species_id=self._id_handler.next_species_id(),
                         generation=0)
        new_sp.members = self.genomes[:]
        for m in new_sp.members:
            m.species_id = new_sp.id
        new_sp.random_representative()
        self._species = {new_sp.id: new_sp}

    def fittest(self):
        """ TODO """
        return self.genomes[int(np.argmax([g.fitness for g in self.genomes]))]

    def update_ids(self):
        # todo
        # checking if the innovation ids should be reset
        if (self.config.reset_innovations_period is not None
                and self._id_handler.reset_counter > self.config.reset_innovations_period):
            self._id_handler.reset()
        self._id_handler.reset_counter += 1

    def evolve(self, generations, fitness_function):
        """

        TODO: remove genomes without enabled connections to the output nodes?

        :param generations:
        :param fitness_function:
        :return:
        """
        # caching the rank-selection probability distribution
        self._calc_prob_dist()

        # evolving
        for generation_num in range(generations):
            # resetting genomes
            # for genome in self.genomes:
            #     genome.reset_activations()

            print(f"[{100*(generation_num + 1) / generations :.2f}%] "
                  f"Generation {generation_num+1} of {generations}.\n"
                  f"Number of species: {len(self._species)}")

            # calculating fitness
            print("Calculating fitness... ", end="")
            fitness_results = self._scheduler.run(items=self.genomes,
                                                  func=fitness_function)

            # assigning fitness and adjusted fitness
            for genome, fitness in zip(self.genomes, fitness_results):
                genome.fitness = fitness
                sp = self._species[genome.species_id]
                genome.adj_fitness = genome.fitness / len(sp.members)
            print("done!")

            # info
            best = self.genomes[int(np.argmax([g.fitness
                                               for g in self.genomes]))]
            print(f"Best fitness: {best.fitness}")
            print("Avg. population fitness: "
                  f"{np.mean([g.fitness for g in self.genomes])}")

            # reproduction and speciation
            print("Reproduction... ", end="")
            self.reproduction()
            print("done!\nInvalid genomes replaced: "
                  f"{self._invalid_genomes_replaced}")
            print("Speciation... ", end="")
            self.speciation(generation=generation_num)
            print(f"done!")
            print("\n" + "#" * 30 + "\n")

    def _generate_offspring(self,
                            species: Species,
                            rank_prob_dist: np.array) -> Genome:
        """ TODO

        Args:
            species:
            rank_prob_dist:

        Returns:

        """
        g1 = np.random.choice(species.members, p=rank_prob_dist)
        baby_id = self._id_handler.next_genome_id()

        # mating / cross-over
        if utils.chance(self.config.mating_chance):
            # interspecific
            if (len(self._species) > 1
                    and utils.chance(self.config.interspecies_mating_chance)):
                g2 = np.random.choice([g for g in self.genomes
                                       if g.species_id != species.id])
            # intraspecific
            else:
                g2 = np.random.choice(species.members)
            baby = mate_genomes(g1, g2, baby_id)
        # binary_fission
        else:
            baby = g1.deep_copy(baby_id)

        # enable connection mutation
        if utils.chance(self.config.enable_connection_mutation_chance):
            baby.enable_random_connection()

        # weight mutation
        if utils.chance(self.config.weight_mutation_chance):
            baby.mutate_weights()

        # new connection mutation
        if utils.chance(self.config.new_connection_mutation_chance):
            baby.add_random_connection(self._id_handler)

        # new node mutation
        if utils.chance(self.config.new_node_mutation_chance):
            baby.add_random_hidden_node(self._id_handler)

        # checking genome validity
        valid_out = (not self.config.infanticide_output_nodes
                     or baby.valid_out_nodes())
        valid_in = (not self.config.infanticide_input_nodes
                    or baby.valid_in_nodes())

        # genome is valid
        if valid_out and valid_in:
            return baby

        # invalid genome: replacing with a new random genome
        self._invalid_genomes_replaced += 1
        return Genome.random_genome(
            num_inputs=self._num_inputs,
            num_outputs=self._num_outputs,
            id_handler=self._id_handler,
            config=self.config,
            hidden_nodes_bounds=self.__mmh_nodes,
            hidden_connections_bounds=self.__mmh_connections)

    def _calc_prob_dist(self):
        """
        TODO
        """
        alpha = self.config.rank_prob_dist_coefficient
        self._rank_prob_dist = np.zeros(len(self.genomes))

        self._rank_prob_dist[0] = 1 - 1 / alpha
        for i in range(1, len(self.genomes)):
            p = self._rank_prob_dist[i - 1] / alpha
            if p < 1e-9:
                break
            self._rank_prob_dist[i] = p

    def reproduction(self):
        """

        :return:
        """
        new_pop = []

        # elitism
        for sp in self._species.values():
            sp.members.sort(key=lambda genome: genome.fitness,
                            reverse=True)

            # preserving the most fit individual
            if len(sp.members) >= self.config.species_elitism_threshold:
                new_pop.append(sp.members[0])

            # removing the least fit individuals
            r = int(len(sp.members) * self.config.weak_genomes_removal_pc)
            if 0 < r < len(sp.members):
                r = len(sp.members) - r
                for g in sp.members[r:]:
                    self.genomes.remove(g)
                sp.members = sp.members[:r]

        # todo: disallow members of species that haven't been improving to
        #  reproduce

        # calculating the number of children for each species
        offspring_count = self._offspring_proportion(
            num_offspring=self._size - len(new_pop)
        )

        # updating mmh nodes and connections (for generating random genomes)
        self.__update_mmh_nodes()
        self.__update_mmh_connections()
        self._invalid_genomes_replaced = 0

        # creating new genomes
        for sp in self._species.values():
            # reproduction probabilities (rank-based selection)
            prob = self._rank_prob_dist[:len(sp.members)]
            prob_sum = np.sum(prob)

            if abs(prob_sum - 1) > 1e-8:
                # normalizing distribution
                prob = prob / prob_sum

            # generating offspring
            babies = [self._generate_offspring(species=sp,
                                               rank_prob_dist=prob)
                      for _ in range(offspring_count[sp.id])]
            new_pop += babies

        assert len(new_pop) == self._size
        self.genomes = new_pop
        self.update_ids()

    def __update_mmh_nodes(self):
        """
        todo
        Returns:

        """
        nums = [len(g.hidden_nodes) for g in self.genomes]
        self.__mmh_nodes = (np.min(nums), np.max(nums))

    def __update_mmh_connections(self):
        """ mmh = min-max hidden
        TODO
        Returns:

        """
        min_hcon = max_hcon = 0
        for g in self.genomes:
            count = 0
            for c in g.connections:
                if c.enabled and (c.from_node.Type == NodeGene.Type.HIDDEN
                                  or c.to_node.Type == NodeGene.Type.HIDDEN):
                    count += 1
            min_hcon = min(min_hcon, count)
            max_hcon = max(max_hcon, count)
        self.__mmh_connections = (min_hcon, max_hcon)

    def _offspring_proportion(self, num_offspring):
        """ Roulette wheel selection. """
        adj_fitness = {sp.id: sp.avg_fitness() for sp in self._species.values()}
        total_adj_fitness = np.sum(list(adj_fitness.values()))

        offspring_count = {}
        count = num_offspring
        for sid in self._species:
            offspring_count[sid] = int(num_offspring * adj_fitness[sid] / total_adj_fitness)
            count -= offspring_count[sid]

        for _ in range(count):
            sid = np.random.choice(list(self._species.keys()))
            offspring_count[sid] += 1

        assert np.sum(list(offspring_count.values())) == num_offspring
        return offspring_count

    def speciation(self, generation):
        """
        "Each existing species is represented by a random genome inside the
        species from the previous generation. A given genome g in the current
        generation is placed in the first species in which g is compatible with
        the representative genome of that species. This way, species do not
        overlap. If g is not compatible with any existing species, a new species
        is created with g as its representative." - Stanley, K. O.
        """
        extinction_threshold = self.config.species_no_improvement_limit

        # checking improvements and resetting members
        removed_sids = []
        for sp in self._species.values():
            past_best_fitness = sp.best_fitness
            sp.best_fitness = sp.fittest().fitness

            if past_best_fitness is not None:
                if sp.best_fitness > past_best_fitness:
                    # updating improvement record
                    sp.last_improvement = generation
                elif (generation - sp.last_improvement) > extinction_threshold:
                    # marking species for extinction (it hasn't shown
                    # improvements in the past few generations)
                    removed_sids.append(sp.id)

            # resetting members
            sp.members = []

        # extinction of unfit species
        for sid in removed_sids:
            self._species.pop(sid)

        # assigning genomes to species
        dist_threshold = self.config.species_distance_threshold
        for genome in self.genomes:
            chosen_species = None

            # checking compatibility with existing species
            for sp in self._species.values():
                if genome.distance(sp.representative) <= dist_threshold:
                    chosen_species = sp
                    break

            # creating a new species, if needed
            if chosen_species is None:
                sid = self._id_handler.next_species_id()
                chosen_species = Species(species_id=sid,
                                         generation=generation)
                chosen_species.representative = genome
                self._species[chosen_species.id] = chosen_species

            # adding genome to species
            chosen_species.members.append(genome)
            genome.species_id = chosen_species.id

        # deleting empty species and updating representatives
        for sp in list(self._species.values()):
            if len(sp.members) == 0:
                self._species.pop(sp.id)
            else:
                sp.random_representative()

    def info(self):
        no_hnode = invalid_out = no_cons = 0
        for g in self.genomes:
            invalid_out += 0 if g.valid_out_nodes() else 1
            no_hnode += 1 if len(g.hidden_nodes) == 0 else 0
            no_cons += (0 if [c for c in g.connections
                              if (c.enabled and not c.self_connecting())]
                        else 1)

        return (f"Size: {len(self.genomes)}\n"
                f"Species: {len(self._species)}\n"
                f"Invalid genomes (out nodes): {invalid_out}\n"
                f"No-hidden node genomes: {no_hnode}\n"
                f"No enabled connection (ignore self connections): {no_cons}")