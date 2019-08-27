import json
import random
import re
from datetime import datetime, timedelta

from fantom_util.constants import JOB_EXPIRY_IN_HOURS
from fantom_util.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    ARRAY,
    UniqueConstraint,
    func,
    select,
    cast,
    Float,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import expression
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, column_property, aliased
from sqlalchemy_utils import LtreeType, Ltree


class BasicMixin(object):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Job(Base, BasicMixin):
    __tablename__ = "job"
    node_utterances = relationship(
        "NodeUtterance",
        secondary="job_node_utterance",
        order_by="JobNodeUtterance.position",
    )
    is_user = Column(Boolean)
    job_type = Column(String, default="system")
    persona_sample = Column(ARRAY(String), default=[])
    node_utterance_worker_jobs = relationship(
        "NodeUtteranceWorkerJob", backref="job", lazy="joined"
    )
    incoherent_node_utterance_worker_jobs = relationship(
        "IncoherentNodeUtteranceWorkerJob", backref="job"
    )
    external_id = Column(UUID(as_uuid=True), server_default=text("uuid_generate_v4()"))

    @hybrid_property
    def is_expired(self):
        return (
            self.created_at + timedelta(hours=JOB_EXPIRY_IN_HOURS) < datetime.now()
            or self.node_utterance_worker_jobs
        )

    @is_expired.expression
    def is_expired(cls):
        return (
            func.dateadd(cls.created_at, text(f"interval {JOB_EXPIRY_IN_HOURS} day"))
            < func.now()
            or func.count(cls.node_utterance_worker_jobs) > 0
        )


class JobNodeUtterance(Base, BasicMixin):
    __tablename__ = "job_node_utterance"
    job_id = Column("job_id", Integer, ForeignKey("job.id"), index=True)
    node_utterance_id = Column(
        "node_utterance_id", Integer, ForeignKey("node_utterance.id")
    )
    position = Column(Integer)


class Worker(Base, BasicMixin):
    __tablename__ = "worker"
    __table_args__ = (
        UniqueConstraint(
            "external_worker_id", "source", name="_external_worker_id_source_uc"
        ),
    )
    external_worker_id = Column(String)
    blocked = Column(Boolean)
    source = Column(String, default="")
    node_utterance_worker_jobs = relationship(
        "NodeUtteranceWorkerJob", backref="worker"
    )
    incoherent_node_utterance_worker_jobs = relationship(
        "IncoherentNodeUtteranceWorkerJob", backref="worker"
    )
    has_more_than_20_qualifaction = Column(
        Boolean, default=False, server_default=expression.false()
    )

    @hybrid_property
    def job_counts(self):
        return len(self.incoherent_node_utterance_worker_jobs) + len(
            self.node_utterance_worker_jobs
        )


class IncoherentNodeUtteranceWorkerJob(Base, BasicMixin):
    __tablename__ = "incoherent_node_utterance_worker_job"
    worker_id = Column(Integer, ForeignKey("worker.id"), index=True)
    job_id = Column(Integer, ForeignKey("job.id"), index=True)
    node_utterance_id = Column(Integer, ForeignKey("node_utterance.id"), index=True)
    assignment_id = Column(String)
    hit_id = Column(String, index=True)


class NodeUtteranceWorkerJob(Base, BasicMixin):
    __tablename__ = "node_utterance_worker_job"
    worker_id = Column(Integer, ForeignKey("worker.id"), index=True)
    job_id = Column(Integer, ForeignKey("job.id"), index=True)
    node_utterance_id = Column(Integer, ForeignKey("node_utterance.id"), index=True)
    assignment_id = Column(String)
    hit_id = Column(String, index=True)


class Node(Base, BasicMixin):
    __tablename__ = "node"
    parent_id = Column(Integer, ForeignKey("node.id"), index=True)
    parent = relationship(
        "Node", backref="children", remote_side="Node.id", lazy="joined"
    )
    _path = Column(LtreeType, server_default="")
    visited_count = Column(Integer, default=1, index=True)
    utterances = relationship("Utterance", secondary="node_utterance", lazy="joined")
    node_utterances = relationship("NodeUtterance", lazy="joined")
    species = Column(String)
    active = Column(Boolean, default=True, index=True)
    path_length = column_property(func.nlevel(_path), deferred=False)

    @hybrid_property
    def is_anonymous(self):
        return any([x.amazon_anonymous for x in self.utterances])

    @hybrid_method
    def recalculate_path(self):
        def recur_parent(node):
            path = [node.id]
            if node.parent:
                return recur_parent(node.parent) + path
            return path

        return recur_parent(self)

    @hybrid_property
    def active_child_count(self):
        return len([x for x in self.children if x.active])

    @active_child_count.expression
    def active_child_count(cls):
        q = aliased(cls)
        return (
            select([cast(func.count("id"), Float)])
            .select_from(q)
            .where(q.parent_id == cls.id)
            .where(q.active.is_(True))
            .label("child_count")
        )

    @hybrid_property
    def child_count(self):
        return len(self.children)

    @child_count.expression
    def child_count(cls):
        q = aliased(cls)
        return (
            select([cast(func.count("id"), Float)])
            .select_from(q)
            .where(q.parent_id == cls.id)
            .label("child_count")
        )

    @staticmethod
    def calculate_score(rand, visits):
        return (rand * 0.2 * visits) + visits

    @property
    def path(self):
        if self._path:
            return [int(x) for x in str(self._path).split(".")]
        return []

    @path.setter
    def path(self, value):
        if value:
            if type(value) == list:
                self._path = Ltree(".".join(map(str, value)))
            else:
                self._path = Ltree(str(value))

    @hybrid_property
    def is_user(self):
        return len(self._path) % 2 == 1

    @is_user.expression
    def is_user(cls):
        return func.mod(func.nlevel(cls._path), 2) == 1

    @hybrid_property
    def score(self):
        visits = self.visited_count
        return Node.calculate_score(random.random(), visits)

    @score.expression
    def score(cls):
        number_of_visits = cast(cls.visited_count.label("number_of_visits"), Float)
        return Node.calculate_score(func.random(), number_of_visits)

    @hybrid_property
    def is_incoherent(self):
        return any(
            [x for x in self.node_utterances if x.incoherent_node_utterance_statuses]
        )


class Utterance(Base, BasicMixin):
    __tablename__ = "utterance"
    utterance_text = Column(String, index=True)
    node_utterances = relationship("NodeUtterance", lazy="select")
    nodes = relationship("Node", secondary="node_utterance", lazy="select")
    amazon_anonymous = Column(
        Boolean,
        server_default=expression.false(),
        default=False,
        nullable=False,
        index=True,
    )
    is_spellchecked = Column(Boolean)


class TTS(Base, BasicMixin):
    __tablename__ = "tts"
    url = Column(String)
    utterance_id = Column(Integer, ForeignKey("utterance.id"))
    is_user = Column(Boolean)


class NodeUtterance(Base, BasicMixin):
    __tablename__ = "node_utterance"
    node_id = Column(Integer, ForeignKey("node.id"), index=True)
    node = relationship("Node", lazy="joined")
    utterance_id = Column(Integer, ForeignKey("utterance.id"), index=True)
    utterance = relationship("Utterance", lazy="joined")
    tts_id = Column(Integer, ForeignKey("tts.id"))
    source = Column(String, default="typed", index=True)
    with_audio = Column(Boolean)
    corrected = Column(Boolean)
    used_text_as_input = Column(Boolean)
    node_utterance_worker_job = relationship(
        "NodeUtteranceWorkerJob", uselist=False, backref="node_utterance", lazy="select"
    )
    incoherent_node_utterance_worker_jobs = relationship(
        "IncoherentNodeUtteranceWorkerJob", backref="node_utterance", lazy="select"
    )
    incoherent_node_utterance_statuses = relationship(
        "NodeUtteranceStatus",
        primaryjoin="and_(NodeUtterance.id==NodeUtteranceStatus.node_utterance_id, NodeUtteranceStatus.status=='incoherent')",
    )


class Training(Base, BasicMixin):
    __tablename__ = "training"
    worker_id = Column(Integer, ForeignKey("worker.id"))
    worker = relationship("Worker")
    tasks = Column(ARRAY(Integer), default=[])


class NodeUtteranceStatus(Base, BasicMixin):
    __tablename__ = "node_utterance_status"
    node_utterance_id = Column(Integer, ForeignKey("node_utterance.id"), index=True)
    node_utterance = relationship(
        "NodeUtterance",
        foreign_keys=[node_utterance_id],
        backref="statuses",
        lazy="select",
    )
    referenced_node_utterance_id = Column(
        "referenced_node_utterance_id", Integer, ForeignKey("node_utterance.id")
    )
    status = Column(String, index=True)
    with_audio = Column(Boolean)
    handled = Column(Boolean, default=False, index=True)


class Merging(Base, BasicMixin):
    __tablename__ = "merging"
    left_node_id = Column(Integer, index=True)
    right_node_id = Column(Integer, index=True)
    merged = Column(Boolean)


class LinkedNodes(Base, BasicMixin):
    __tablename__ = "linked_nodes"
    linked_to_node_id = Column(Integer, index=True)
    linked_from_node_id = Column(Integer, index=True)


class Conversation(Base, BasicMixin):
    __tablename__ = "conversation"
    session_id = Column(String)
    user_utterance = Column(String, index=True)
    transformed_user_utterance = Column(String, index=True)
    system_utterance = Column(String)
    topic = Column(String)
    candidates = Column(String)
    interaction_timestamp = Column(DateTime)
    intent = Column(String)
    sentiment = Column(String)
    user_id = Column(String)
    graphsearch_score = Column(Float)
    history = Column(String)
    named_enteties = Column(String)
    asr_json = Column(String)
    asr_score = Column(Float)
    conversation_id = Column(String, index=True)
    processed = Column(DateTime)
    graphsearch_matched_utt = Column(String)
    graphsearch_matched_node = Column(Integer)
    graphsearch_matched_utterance_id = Column(Integer)
    stage = Column(String)
    lambda_function_version = Column(String)
    graphsearch_node = relationship(
        "Node",
        foreign_keys=[graphsearch_matched_node],
        primaryjoin="Node.id == Conversation.graphsearch_matched_node",
    )
    graphsearch_utterance = relationship(
        "Utterance",
        foreign_keys=[graphsearch_matched_utterance_id],
        primaryjoin="Utterance.id == Conversation.graphsearch_matched_utterance_id",
        lazy="select",
    )

    @hybrid_property
    def used_module(self):
        try:
            json_candidates = json.loads(self.candidates)
            for key, val in json_candidates.items():
                if val == self.system_utterance:
                    return key
        except json.decoder.JSONDecodeError:
            if isinstance(self.system_utterance, str):
                match = re.search(
                    rf'(?:"|{{|,|__)([A-Z]+)__\+__{re.escape(self.system_utterance)}',
                    self.candidates,
                )
                if match:
                    return match.group(1)
        return "OTHER"


class AnonymousUtterance(Base, BasicMixin):
    __tablename__ = "anonymous_utterance"
    text = Column(String)
    appropriate = Column(Boolean)


class Rating(Base, BasicMixin):
    __tablename__ = "rating"
    conversation_id = Column(String, index=True)
    start_time = Column(DateTime)
    rating = Column(Float)
    turns = Column(Integer)
    graphsearch_ratio = Column(Float)
    evi_ratio = Column(Float)
    fallback_ratio = Column(Float)
    safetyfilter_ratio = Column(Float)
    common_ratio = Column(Float)
    other_ratio = Column(Float)
    feedback = Column(String)
    named_entities = Column(ARRAY(String), default=[])
    rating_utterance_rows = relationship(
        "RatingUtteranceRow", order_by="RatingUtteranceRow.turn_number", lazy="joined"
    )
    turn_error = Column(Integer)

    @hybrid_property
    def avg_amazon_rating(self):
        ratings = []
        for row in self.rating_utterance_rows:
            if row.response_quality:
                ratings.append(float(row.response_quality))
        if ratings:
            return sum(ratings) / len(ratings)
        return None

    @hybrid_property
    def avg_graphsearch_score(self):
        score = []
        for row in self.rating_utterance_rows:
            if row.conversation.graphsearch_score:
                score.append(float(row.conversation.graphsearch_score))
        if score:
            return sum(score) / len(score)
        return None

    @hybrid_property
    def has_amazon_topic_annotations(self):
        for row in self.rating_utterance_rows:
            if (
                row.user_utterance_topic
                or row.user_utterance_intent
                or row.system_utterance_topic
                or row.system_utterance_intent
            ):
                return True
        return False


class RatingUtteranceRow(Base, BasicMixin):
    __tablename__ = "rating_utterance_row"
    rating_id = Column(Integer, ForeignKey("rating.id"), index=True)
    rating = relationship("Rating")
    conversation_id = Column(Integer, ForeignKey("conversation.id"), index=True)
    conversation = relationship("Conversation", lazy="joined")
    turn_number = Column(Integer)
    user_utterance_topic = Column(String)
    user_utterance_intent = Column(String)
    system_utterance_topic = Column(String)
    system_utterance_intent = Column(String)
    response_quality = Column(Integer)
    is_coherent = Column(Boolean)
    is_engaging = Column(Boolean)
    file_name = Column(String)


class RootNode(Base, BasicMixin):
    __tablename__ = "root_node"
    node_id = Column(Integer)
    is_root_node = Column(Boolean)
    utterance = Column(String)


class PotentialNodeMerge(Base, BasicMixin):
    __tablename__ = "potential_node_merge"
    left_node_id = Column(Integer)
    right_node_id = Column(Integer)
    score = Column(Float)
